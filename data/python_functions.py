# Python Functions for Data Processing

def load_data_from_csv(file_path):
    """
    Load data from a CSV file using pandas.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pandas.DataFrame: Loaded data
    """
    import pandas as pd
    return pd.read_csv(file_path)

def clean_text_data(text):
    """
    Clean and preprocess text data.
    
    Args:
        text (str): Raw text to clean
        
    Returns:
        str: Cleaned text
    """
    import re
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip().lower()

def calculate_statistics(data):
    """
    Calculate basic statistics for numerical data.
    
    Args:
        data (list): List of numerical values
        
    Returns:
        dict: Statistics including mean, median, std
    """
    import statistics
    return {
        'mean': statistics.mean(data),
        'median': statistics.median(data),
        'std': statistics.stdev(data),
        'min': min(data),
        'max': max(data)
    }

def create_visualization(x_data, y_data, title="Chart"):
    """
    Create a simple line plot visualization.
    
    Args:
        x_data (list): X-axis data points
        y_data (list): Y-axis data points
        title (str): Chart title
    """
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 6))
    plt.plot(x_data, y_data)
    plt.title(title)
    plt.xlabel('X Values')
    plt.ylabel('Y Values')
    plt.grid(True)
    plt.show()

class DataProcessor:
    """
    A class for processing and analyzing data.
    """
    
    def __init__(self, data):
        self.data = data
        self.processed_data = None
    
    def process(self):
        """Process the raw data."""
        # Example processing logic
        self.processed_data = [x * 2 for x in self.data if isinstance(x, (int, float))]
        return self.processed_data
    
    def get_summary(self):
        """Get a summary of the data."""
        if self.processed_data is None:
            self.process()
        
        return {
            'total_items': len(self.processed_data),
            'sum': sum(self.processed_data),
            'average': sum(self.processed_data) / len(self.processed_data) if self.processed_data else 0
        }
