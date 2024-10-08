from typing import Iterator
import torch
from torch import nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd


DATA_SOURCE_PATH = '../../data/processed/pscalar/neural_gbc_nn.csv'

# Check if CUDA is available
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class CustomDatasetFromDF(Dataset):
    """Custom dataset class for loading data from a pandas dataframe.

    Args:
        dataframe (pd.DataFrame): The dataframe containing the data.

    Parameters:
        dataframe (pd.DataFrame): The dataframe containing the data.
        target_columns (pd.Index): The columns containing the target values.
    """
    def __init__(self, dataframe):
        self.dataframe = dataframe
        self.dataframe.drop(columns=['Group', 'id'], inplace=True)
        PANSS_selector = dataframe.columns[dataframe.columns.str.contains('PANSS')]
        self.target_columns = PANSS_selector

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, index):
        neural_vector = torch.tensor(self.dataframe.drop(columns=self.target_columns).iloc[index].values, dtype=torch.float)
        targets = torch.tensor(self.dataframe[self.target_columns].iloc[index].values, dtype=torch.float)
        return neural_vector, targets
    
class CustomDatasetFromNumpy(Dataset):
    """Custom dataset class for loading data from a numpy array.
    
    Args:
        data (np.ndarray): The data.
        targets (np.ndarray): The target values.

    Parameters:
        data (np.ndarray): The data.
        targets (np.ndarray): The target values.
    """
    def __init__(self, data, targets):
        self.data = torch.tensor(data, dtype=torch.float)
        self.targets = torch.tensor(targets, dtype=torch.float)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index], self.targets[index]


class NeuralEncoder(nn.Module):
    """A simple neural network 2D encoder for the GBC data.
    
    Args:
        activation (torch.nn.Module): The activation function to use.
    
    Parameters:
        activation (torch.nn.Module): The activation function to use.
        encoder (torch.nn.Linear): The first linear layer.
        hidden1 (torch.nn.Linear): The second linear layer.
        hidden2 (torch.nn.Linear): The third linear layer.
        decoder (torch.nn.Linear): The fourth linear layer.
    """
    def __init__(self, activation=nn.ReLU()):
        super(NeuralEncoder, self).__init__()
        self.activation = activation
        input_dim = 718
        hidden_dim = 128
        output_dim = 30
        self.encoder = nn.Linear(input_dim, hidden_dim, device=device)
        self.hidden1 = nn.Linear(hidden_dim, 2, device=device)
        self.hidden2 = nn.Linear(2, hidden_dim, device=device)
        self.decoder = nn.Linear(hidden_dim, output_dim, device=device)

    def forward(self, x):
        """Forward pass of the neural network.

        Args:
            x (torch.Tensor): The input data.
        
        Returns:
            torch.Tensor: The output of the neural network.
        """
        x = x.to(device)
        x = self.activation(self.encoder(x))
        x = self.activation(self.hidden1(x))
        x = self.activation(self.hidden2(x))
        x = self.activation(self.decoder(x))
        return x
    
    def train_model(self, dataloader, epochs=10, lr=0.01):
        self.to(device)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.parameters(), lr=lr)
        for epoch in range(epochs):
            for data, targets in dataloader:
                data, targets = data.to(device), targets.to(device)
                optimizer.zero_grad()
                output = self(data)
                loss = criterion(output, targets)
                loss.backward()
                optimizer.step()
            print(f'Epoch {epoch+1}, Loss: {loss.item()}')
        print('Training complete!')
        return self
    
    def predict(self, data):
        """Predict the output of the neural network.

        Args:
            data (torch.Tensor): The input data.
        
        Returns:
            torch.Tensor: The output of the neural network.
        """
        self.to(device)
        self.eval()
        data = data.to(device)
        with torch.no_grad():
            return self(data)
        

        
    def generate_embedding(self, data):
        """Generate the embeddings of the input data.

        Args:
            data (np.ndarray): The input data.
        
        Returns:
            np.ndarray: The embeddings of the input data.
        """
        data = torch.tensor(data, dtype=torch.float)
        self.to(device)
        self.eval()
        data = data.to(device)
        with torch.no_grad():
            embds = self.activation(self.encoder(data))
            embds = self.activation(self.hidden1(embds))
            return embds.cpu().numpy()


class Neural3DEncoder(nn.Module):
    """Neural network for the 3D embeddings of the GBC data.

    Args:
        activation (torch.nn.Module): The activation function to use.
    
    Parameters:
        activation (torch.nn.Module): The activation function to use.
        encoder (torch.nn.Linear): The first linear layer.
        hidden1 (torch.nn.Linear): The second linear layer.
        hidden2 (torch.nn.Linear): The third linear layer.
        decoder (torch.nn.Linear): The fourth linear layer.
    """
    def __init__(self, activation=nn.ReLU()):
        super(Neural3DEncoder, self).__init__()
        self.activation = activation
        input_dim = 718
        hidden_dim = 128
        output_dim = 30
        self.encoder = nn.Linear(input_dim, hidden_dim, device=device)
        self.hidden1 = nn.Linear(hidden_dim, 3, device=device)
        self.hidden2 = nn.Linear(3, hidden_dim, device=device)
        self.decoder = nn.Linear(hidden_dim, output_dim, device=device)

    def forward(self, x):
        """Forward pass of the neural network.

        Args:
            x (torch.Tensor): The input data.
        
        Returns:
            torch.Tensor: The output of the neural network.
        """
        x = x.to(device)
        x = self.activation(self.encoder(x))
        x = self.activation(self.hidden1(x))
        x = self.activation(self.hidden2(x))
        x = self.activation(self.decoder(x))
        return x
    
    def train_model(self, dataloader, epochs=10, lr=0.01):
        """Train the neural network.

        Args:
            dataloader (torch.utils.data.DataLoader): The dataloader.
            epochs (int): The number of epochs.
            lr (float): The learning rate.

        Returns:
            Neural3DEncoder: The trained neural network.
        """
        self.to(device)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.parameters(), lr=lr)
        for epoch in range(epochs):
            for data, targets in dataloader:
                data, targets = data.to(device), targets.to(device)
                optimizer.zero_grad()
                output = self(data)
                loss = criterion(output, targets)
                loss.backward()
                optimizer.step()
            print(f'Epoch {epoch+1}, Loss: {loss.item()}')
        print('Training complete!')
        return self
    
    def predict(self, data):
        """Predict the output of the neural network.

        Args:
            data (torch.Tensor): The input data.

        Returns:
            torch.Tensor: The output of the neural network.
        """
        self.to(device)
        self.eval()
        data = data.to(device)
        with torch.no_grad():
            return self(data)
        
    def generate_embedding(self, data):
        """Generate the embeddings of the input data.

        Args:
            data (np.ndarray): The input data.
        
        Returns:
            np.ndarray: The embeddings of the input data.
        """
        data = torch.tensor(data, dtype=torch.float)
        self.to(device)
        self.eval()
        data = data.to(device)
        with torch.no_grad():
            embds = self.activation(self.encoder(data))
            embds = self.activation(self.hidden1(embds))
            return embds.cpu().numpy()
        

class NeuralEncoderDeep(nn.Module):
    """
    A deeper neural network to generate 2D embeddings of the GBC data.

    Args:
        activation (torch.nn.Module): The activation function to use.

    Parameters:
        activation (torch.nn.Module): The activation function to use.
        encoder (torch.nn.Linear): The first linear layer.
        hidden1 (torch.nn.Linear): The second linear layer.
        hidden2 (torch.nn.Linear): The third linear layer.
        hidden3 (torch.nn.Linear): The fourth linear layer.
        hidden4 (torch.nn.Linear): The fifth linear layer.
        decoder (torch.nn.Linear): The sixth linear layer.
    """
    def __init__(self, activation=nn.ReLU()):
        super(NeuralEncoderDeep, self).__init__()
        self.activation = activation
        input_dim = 718
        hidden_dim_1 = 256
        hidden_dim_2 = 64
        output_dim = 30
        self.encoder = nn.Linear(input_dim, hidden_dim_1, device=device)
        self.hidden1 = nn.Linear(hidden_dim_1, hidden_dim_2, device=device)
        self.hidden2 = nn.Linear(hidden_dim_2, 2, device=device)
        self.hidden3 = nn.Linear(2, hidden_dim_2, device=device)
        self.hidden4 = nn.Linear(hidden_dim_2, hidden_dim_1, device=device)
        self.decoder = nn.Linear(hidden_dim_1, output_dim, device=device)

    def forward(self, x):
        """Forward pass of the neural network.
        
        Args:
            x (torch.Tensor): The input data.
            
        Returns:
            torch.Tensor: The output of the neural network.
        """
        x = x.to(device)
        x = self.activation(self.encoder(x))
        x = self.activation(self.hidden1(x))
        x = self.activation(self.hidden2(x))
        x = self.activation(self.hidden3(x))
        x = self.activation(self.hidden4(x))
        x = self.activation(self.decoder(x))
        return x
    
    def predict(self, data):
        """Predict the output of the neural network.

        Args:
            data (torch.Tensor): The input data.
        
        Returns:
            torch.Tensor: The output of the neural network.
        """
        self.to(device)
        self.eval()
        data = data.to(device)
        with torch.no_grad():
            return self(data)
        
    def generate_embedding(self, data):
        """Generate the embeddings of the input data.

        Args:
            data (np.ndarray): The input data.
        
        Returns:
            np.ndarray: The embeddings of the input data.
        """
        data = torch.tensor(data, dtype=torch.float)
        self.to(device)
        self.eval()
        data = data.to(device)
        with torch.no_grad():
            embds = self.activation(self.encoder(data))
            embds = self.activation(self.hidden1(embds))
            return embds.cpu().numpy()
        
class Neural3DEncoderDeep(nn.Module):
    """A deeper neural network to generate 3D embeddings of the GBC data.

    Args:
        activation (torch.nn.Module): The activation function to use.
    
    Parameters:
        activation (torch.nn.Module): The activation function to use.
        encoder (torch.nn.Linear): The first linear layer.
        hidden1 (torch.nn.Linear): The second linear layer.
        hidden2 (torch.nn.Linear): The third linear layer.
        hidden3 (torch.nn.Linear): The fourth linear layer.
        hidden4 (torch.nn.Linear): The fifth linear layer.
        decoder (torch.nn.Linear): The sixth linear layer.
    """
    def __init__(self, activation=nn.ReLU()):
        super(Neural3DEncoderDeep, self).__init__()
        self.activation = activation
        input_dim = 718
        hidden_dim_1 = 256
        hidden_dim_2 = 64
        output_dim = 30
        self.encoder = nn.Linear(input_dim, hidden_dim_1, device=device)
        self.hidden1 = nn.Linear(hidden_dim_1, hidden_dim_2, device=device)
        self.hidden2 = nn.Linear(hidden_dim_2, 3, device=device)
        self.hidden3 = nn.Linear(3, hidden_dim_2, device=device)
        self.hidden4 = nn.Linear(hidden_dim_2, hidden_dim_1, device=device)
        self.decoder = nn.Linear(hidden_dim_1, output_dim, device=device)

    def forward(self, x):
        """Forward pass of the neural network.

        Args:
            x (torch.Tensor): The input data.
        
        Returns:
            torch.Tensor: The output of the neural network.
        """
        x = x.to(device)
        x = self.activation(self.encoder(x))
        x = self.activation(self.hidden1(x))
        x = self.activation(self.hidden2(x))
        x = self.activation(self.hidden3(x))
        x = self.activation(self.hidden4(x))
        x = self.activation(self.decoder(x))
        return x
    
    def predict(self, data):
        """Predict the output of the neural network.

        Args:
            data (torch.Tensor): The input data.

        Returns:
            torch.Tensor: The output of the neural network.
        """
        self.to(device)
        self.eval()
        data = data.to(device)
        with torch.no_grad():
            return self(data)
        
    def generate_embedding(self, data):
        """Generate the embeddings of the input data.

        Args:
            data (np.ndarray): The input data.
        
        Returns:
            np.ndarray: The embeddings of the input data.
        """
        data = torch.tensor(data, dtype=torch.float)
        self.to(device)
        self.eval()
        data = data.to(device)
        with torch.no_grad():
            embds = self.activation(self.encoder(data))
            embds = self.activation(self.hidden1(embds))
            return embds.cpu().numpy()



if __name__ == '__main__':
    """ Main function used for testing the neural encoder.
    """

    # Load the dataset
    dataset_pd = pd.read_csv(DATA_SOURCE_PATH)
    print(dataset_pd.columns)
    
    # Create a custom dataset and dataloader
    custom_dataset = CustomDatasetFromDF(dataset_pd.copy())
    dataloader = DataLoader(custom_dataset, batch_size=16, shuffle=True)
    
    # Train the neural encoder
    neural_encoder = NeuralEncoder()
    neural_encoder = neural_encoder.train_model(dataloader, epochs=10, lr=0.01)
    
    # Generate the embeddings
    PANSS_selector = dataset_pd.columns[dataset_pd.columns.str.contains('PANSS')]
    X = dataset_pd.drop(columns=list(PANSS_selector)+['Group', 'id']).values
    print(neural_encoder.generate_embedding(X))
