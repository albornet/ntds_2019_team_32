import matplotlib.pyplot as plt
import warnings
import numpy
import torch
import sys
import os
from sklearn.linear_model import LogisticRegression
from scipy.interpolate    import CubicSpline


def compute_laplacian(adjacency: numpy.ndarray, normalize: bool):
    degrees = adjacency.sum(axis=0)
    L = numpy.diag(degrees) - adjacency
    if normalize:
        norm_vector = numpy.sqrt(degrees)
        norm_matrix = numpy.outer(norm_vector, norm_vector)
        norm_matrix[norm_matrix==0] = 1.0  # avoid NaN values for unconnected nodes
        return L/norm_matrix
    else:
        return L


def spectral_decomposition(laplacian: numpy.ndarray):
    eig_vals, eig_vects = numpy.linalg.eigh(laplacian)
    ordered_indexes     = eig_vals.argsort()
    return eig_vals[ordered_indexes], eig_vects[:, ordered_indexes]


def compute_number_connected_components(lamb: numpy.array, threshold: float):
    n_components = len(lamb[lamb<threshold])
    return n_components


def GFT(signal: numpy.ndarray):
    return U.transpose() @ signal


def iGFT(fourier_coefficients: numpy.ndarray):
    return U @ fourier_coefficients


def fit_polynomial(lam: numpy.ndarray, order: int, spectral_response: numpy.ndarray):
    V = numpy.vander(lam, order+1, increasing=True)
    return numpy.real(numpy.linalg.lstsq(V, spectral_response, rcond=None)[0])


def polynomial_graph_filter(coeff: numpy.array, laplacian: numpy.ndarray):
    response = numpy.zeros(laplacian.shape)
    L_k      = numpy.identity(laplacian.shape[0])
    for c in coeff:
        response += c*L_k
        L_k = L_k @ laplacian
    return response


def polynomial_graph_filter_response(coeff: numpy.array, lam: numpy.ndarray):
    response = numpy.zeros(lam.shape)
    for i, c in enumerate(coeff):
        response += c*numpy.real(lam)**i
    return response


class LogisticRegression(torch.nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dim=64):
        super(LogisticRegression, self).__init__()
        self.encode = torch.nn.Linear(input_dim,  hidden_dim)
        self.decode = torch.nn.Linear(hidden_dim, output_dim)
        self.relu   = torch.nn.ReLU()
        self.drop   = torch.nn.Dropout(0.5) 


    def forward(self, x):
        latent = self.drop(self.relu(self.encode(x)))
        output = self.relu(self.decode(latent))
        return output


class ConvolutionalRegression(torch.nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dim=64, kernel_size=3):
        super(ConvolutionalRegression, self).__init__()
        self.conv1      = torch.nn.Conv1d( 1,            hidden_dim//4, kernel_size=kernel_size)
        self.conv2      = torch.nn.Conv1d(hidden_dim//4, hidden_dim,    kernel_size=kernel_size)
        self.encode_dim = hidden_dim*(input_dim - 2*(kernel_size-1))
        self.decode     = torch.nn.Linear(self.encode_dim, output_dim)
        self.relu       = torch.nn.ReLU()
        self.drop       = torch.nn.Dropout(0.5) 

    def forward(self, x):
        x = x.unsqueeze(1)
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = x.view([-1,self.encode_dim])
        x = self.drop(x)
        output = self.relu(self.decode(x))
        return output


def evaluate(bt_size, features, labels, model, crit):
    with torch.no_grad():
        n_smpl = features.shape[0]
        n_hits = torch.tensor(0)
        losses = torch.tensor(0.0)
        for i_start in numpy.arange(0, n_smpl, bt_size):
                
            i_end  = min(i_start+bt_size, n_smpl)
            feats  = features[i_start:i_end]
            labs   = labels[  i_start:i_end]
            output = model(feats)
            loss   = crit(output, labs)
            n_hits += (output.argmax(axis=1) == labs).int().sum()
            losses += bt_size*loss

        return 100*n_hits/n_smpl, losses/n_smpl


def train(bt_size, features, labels, model, crit, optim, sched, n_epochs, plot_color=None):
    plot_train_loss = []
    plot_valid_loss = []
    plot_train_hitr = []
    plot_valid_hitr = []
    plot_epoch = []
    for epoch in range(int(n_epochs)):
        n_smpl = features.shape[0]
        n_hits = torch.tensor(0)
        losses = torch.tensor(0.0)
        for i_start in numpy.arange(0, n_smpl, bt_size):
            
            sched.step(epoch + i_start/n_smpl)
            i_end  = min(i_start+bt_size, n_smpl)
            feats  = train_features[i_start:i_end]
            labs   = train_labels[  i_start:i_end]
            optim.zero_grad()
            output = model(feats)
            loss   = crit(output, labs)
            loss.backward()
            optim.step()
            n_hits += (output.argmax(axis=1) == labs).int().sum()
            losses += bt_size*loss

        if epoch % (n_epochs//100) == 0:
            train_hit_rate  = 100*n_hits/n_smpl
            train_mean_loss = losses/n_smpl
            valid_hit_rate, valid_mean_loss = evaluate(bt_size, valid_features, valid_labels, model, crit)
            print('\nEpoch %3i' % (epoch))
            print('\tTraining:   Loss %4.3f - Hit rate %3.1f%%' % (train_mean_loss, train_hit_rate))
            print('\tValidation: Loss %4.3f - Hit rate %3.1f%%' % (valid_mean_loss, valid_hit_rate))
            if epoch != n_epochs-(n_epochs//100):
                sys.stdout.write("\033[4F")
            plot_train_loss.append(train_mean_loss.detach().numpy())
            plot_valid_loss.append(valid_mean_loss.detach().numpy())
            plot_train_hitr.append(train_hit_rate.detach().numpy())
            plot_valid_hitr.append(valid_hit_rate.detach().numpy())
            plot_epoch.append(epoch)

    if plot_color is not None:
        graph_label = ' (without graph)' if plot_color=='b' else ' (with graph)'
        plt.figure(1)
        plt.plot(plot_epoch, plot_train_loss, plot_color+'-' , label='Training loss'+graph_label)
        plt.plot(plot_epoch, plot_valid_loss, plot_color+'--', label='Validation loss'+graph_label)
        plt.legend()
        plt.figure(2)
        plt.plot(plot_epoch, plot_train_hitr, plot_color+'-' , label='Training hit rate'+graph_label)
        plt.plot(plot_epoch, plot_valid_hitr, plot_color+'--', label='Validation hit rate'+graph_label)
        plt.legend()

# Load the datasets (twitter features, scholar labels, coauthorship graph)
remove_lonely_authors = False
twitter_data = numpy.load('twitter_data/twitter_signals.npy')
scholar_data = numpy.load('scholar_data/scholar_signals.npy')
adjacency    = numpy.load('scholar_data/A_coauthors.npy')
if remove_lonely_authors:
    no_coauth = numpy.where(numpy.sum(adjacency, axis=0) != 0)[0]
    adjacency = adjacency[no_coauth][:, no_coauth]

# Create the input features and target labels
twitter_signals  = twitter_data[:,   1:]  # input features
scholar_signals  = scholar_data[:, -14:]  # very hard labels
scholar_hindexes = scholar_data[:,   3 ]  # easier labels

scholar_labels = (scholar_hindexes/10).astype(int)  # every 10, label changes
# scholar_labels = scholar_signals
n_classes = scholar_labels.max()+1
n_samples = scholar_labels.shape[0]

# Create the training, validation and testing sets
n_train = 1000
n_valid = 1000
n_testt = n_samples-(n_train+n_valid)
train_features = torch.FloatTensor(twitter_signals[               :n_train        ].astype(float))
train_labels   = torch.LongTensor( scholar_labels[                :n_train        ].astype(int  ))
valid_features = torch.FloatTensor(twitter_signals[n_train:        n_train+n_valid].astype(float))
valid_labels   = torch.LongTensor( scholar_labels[ n_train:        n_train+n_valid].astype(int  ))
testt_features = torch.FloatTensor(twitter_signals[n_train+n_valid:               ].astype(float))
testt_labels   = torch.LongTensor( scholar_labels[ n_train+n_valid:               ].astype(int  ))

# Some useful numbers
inn_dim  = train_features.shape[1]
out_dim  = n_classes
lr_rate  = 1e-5
bt_size  = 100
n_epochs = 200

# Create a native model and its learning instances
# model = LogisticRegression(inn_dim, out_dim)
model = ConvolutionalRegression(inn_dim, out_dim)
crit  = torch.nn.CrossEntropyLoss()
optim = torch.optim.Adam(model.parameters(), lr=lr_rate)
sched = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optim, 100)

# Train and test the classifier
train(bt_size, train_features, train_labels, model, crit, optim, sched, n_epochs, plot_color='b')
test_hit_rate, test_mean_loss = evaluate(bt_size, testt_features, testt_labels, model, crit)
print('\nTesting: Loss %4.3f - Hit rate %3.1f%%\n' % (test_mean_loss, test_hit_rate))

# Redo the spectral analysis
redo_spectral = True
if redo_spectral:

    # Compute the laplacian of the coauthorship adjacency matrix
    laplacian = compute_laplacian(adjacency, normalize=True)
    lam, U    = spectral_decomposition(laplacian)
    numpy.save('scholar_data/coauthorship_L',   laplacian)
    numpy.save('scholar_data/coauthorship_lam', lam      )
    numpy.save('scholar_data/coauthorship_U',   U        )

    # Compute a filter for the input features, using the graph structure
    ideal_filter = 1.0/(1.0+5.0*lam)
    order        = 5
    coeff        = fit_polynomial(lam, order, ideal_filter)
    graph_filter = polynomial_graph_filter(coeff, laplacian)
    numpy.save('scholar_data/coauthorship_filter', graph_filter)

# Load the results of the spectral analysis
else:
    laplacian    = numpy.load('scholar_data/coauthorship_L.npy'     )
    lam          = numpy.load('scholar_data/coauthorship_lam.npy'   )
    U            = numpy.load('scholar_data/coauthorship_U.npy'     )
    graph_filter = numpy.load('scholar_data/coauthorship_filter.npy')

# Filter the input features and regenerate the training, testing and validation sets
twitter_signals_gcn = graph_filter @ twitter_signals
train_features_gcn  = torch.FloatTensor(twitter_signals_gcn[               :n_train        ].astype(float))
valid_features_gcn  = torch.FloatTensor(twitter_signals_gcn[n_train:        n_train+n_valid].astype(float))
testt_features_gcn  = torch.FloatTensor(twitter_signals_gcn[n_train+n_valid:               ].astype(float))

# Create a new model that will use the graph knowledge
# model_gcn = LogisticRegression(inn_dim, out_dim)
model_gcn = ConvolutionalRegression(inn_dim, out_dim)
crit_gcn  = torch.nn.CrossEntropyLoss()
optim_gcn = torch.optim.Adam(model_gcn.parameters(), lr=lr_rate)
sched_gcn = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optim, 100)

# Train and test the classifier
train(bt_size, train_features_gcn, train_labels, model_gcn, crit_gcn, optim_gcn, sched_gcn, n_epochs, plot_color='r')
test_hit_rate, test_mean_loss = evaluate(bt_size, testt_features_gcn, testt_labels, model_gcn, crit_gcn)
print('\nTesting: Loss %4.3f - Hit rate %3.1f%%\n' % (test_mean_loss, test_hit_rate))
plt.show()
