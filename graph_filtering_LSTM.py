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


class TimeSeriesPredictor(torch.nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dim=1):
        super(TimeSeriesPredictor, self).__init__()
        self.input_dim  = input_dim
        self.output_dim = output_dim
        self.hidden_dim = hidden_dim
        self.lstm       = torch.nn.LSTM(input_size=1, hidden_size=hidden_dim, batch_first=True)
        self.linear     = torch.nn.Linear(hidden_dim, 1)
        # self.decoder    = torch.nn.Linear(input_dim, output_dim)
        self.conv1      = torch.nn.Conv1d(1, 1, kernel_size=3,  stride=2, padding=0)
        self.conv2      = torch.nn.Conv1d(1, 1, kernel_size=7,  stride=2, padding=0)
        self.conv3      = torch.nn.Conv1d(1, 1, kernel_size=13, stride=2, padding=0)
        # self.states = (torch.zeros(1,1,self.hidden_dim), torch.zeros(1,1,self.hidden_dim))

    def forward(self, x):
        
        # states = self.init_states()
        x = self.lstm(x.unsqueeze(-1))[0]
        if self.hidden_dim > 1:
            x = self.linear(x)
        x = self.conv1(x.permute(0,2,1))
        x = self.conv2(x)
        x = self.conv3(x)
        return x.squeeze()


def interpolate_scholar(time_series):
    t  = numpy.arange(0.5, 14.5, 1.0 )  # last year -t corresponds to "June-July 2019"
    ts = numpy.arange(0.0, 14.0, 1/12)  # last month-t corresponds to "December  2019"
    ys = []
    for y in time_series:
        cs = CubicSpline(t,y)
        ys.append((cs(ts)/12).astype(int))

    return ys


def evaluate(bt_size, features, labels, model, crit, plot_stuff=False):
    with torch.no_grad():
        n_smpl = features.shape[0]
        losses = torch.tensor(0.0)
        for i_start in numpy.arange(0, n_smpl, bt_size):
                
            i_end  = min(i_start+bt_size, n_smpl)
            feats  = features[i_start:i_end]
            labs   = labels[  i_start:i_end]
            output = model(feats)
            loss   = crit(output, labs)
            losses += bt_size*loss

        # Plot just once
        if plot_stuff:
            for i in range(10):
                plt.plot(output[i], 'r')
                plt.plot(labels[i], 'b')
                plt.show()

        return losses/n_smpl


def train(bt_size, features, labels, model, crit, optim, sched, n_epochs):
    for epoch in range(int(n_epochs)):
        n_smpl = features.shape[0]
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
            losses += bt_size*loss

        if epoch % (n_epochs//10) == 0:
            train_mean_loss = losses/n_smpl
            valid_mean_loss = evaluate(bt_size, valid_features, valid_labels, model, crit)
            print('\nEpoch %3i' % (epoch))
            print('\tTraining   loss %4.3f' % (train_mean_loss))
            print('\tValidation loss %4.3f' % (valid_mean_loss))
            if epoch != n_epochs-(n_epochs//10):
                sys.stdout.write("\033[4F")


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
twitter_signals  = (twitter_signals - twitter_signals.min())/twitter_signals.std()
scholar_signals  = scholar_data[:, -14:]  # very hard labels
scholar_signals  = (scholar_signals - scholar_signals.min())/scholar_signals.std()
# scholar_signals  = interpolate_scholar(scholar_signals)

scholar_labels = scholar_signals
n_samples      = scholar_labels.shape[0]

# Create the training, validation and testing sets
n_train = 2000
n_valid = 500
n_testt = n_samples-(n_train+n_valid)
train_features = torch.FloatTensor(twitter_signals[                :n_train        ].astype(float))
train_labels   = torch.FloatTensor( scholar_labels[                :n_train        ].astype(float))
valid_features = torch.FloatTensor(twitter_signals[n_train:         n_train+n_valid].astype(float))
valid_labels   = torch.FloatTensor( scholar_labels[n_train:         n_train+n_valid].astype(float))
testt_features = torch.FloatTensor(twitter_signals[n_train+n_valid:                ].astype(float))
testt_labels   = torch.FloatTensor( scholar_labels[n_train+n_valid:                ].astype(float))

# Some useful numbers
inn_dim  = train_features.shape[1]
out_dim  = train_labels.shape[1]
lr_rate  = 1e-4
bt_size  = 100
n_epochs = 1000

# Create a native model and its learning instances
model = TimeSeriesPredictor(inn_dim, out_dim)
crit  = torch.nn.MSELoss()
optim = torch.optim.Adam(model.parameters(), lr=lr_rate)
sched = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optim, 100)

# Train and test the classifier
train(bt_size, train_features, train_labels, model, crit, optim, sched, n_epochs)
test_mean_loss = evaluate(bt_size, testt_features, testt_labels, model, crit, plot_stuff=True)
print('\nTesting: Loss %4.3f\n' % (test_mean_loss))

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
model_gcn = TimeSeriesPredictor(inn_dim, out_dim)
crit_gcn  = torch.nn.MSELoss()
optim_gcn = torch.optim.Adam(model_gcn.parameters(), lr=lr_rate)
sched_gcn = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optim, 100)

# Train and test the classifier
train(bt_size, train_features_gcn, train_labels, model_gcn, crit_gcn, optim_gcn, sched_gcn, n_epochs)
test_mean_loss = evaluate(bt_size, testt_features_gcn, testt_labels, model_gcn, crit_gcn, plot_stuff=True)
print('\nTesting: Loss %4.3f\n' % (test_mean_loss))
