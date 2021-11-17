
import pandas as pd

class FlowsResult():
    def __init__(self, csv, clear=False,
        columns=['flow', 'tid', 'cwnd', 'rate', 'loss', 'sacked', 'acked', 'rtt', 'inflight']):
        self.csv = csv
        self.columns = columns
        self.res = pd.DataFrame(columns=columns)
        if clear:
            self.res.to_csv(csv, index=False)    # clear the file

    def append(self, row, flush_period=30):
        """Appends row df to result. row should be a DataFrame.
        """
        assert len(row[0]) == len(self.columns)
        row_df = pd.DataFrame(row, columns=self.columns)
        self.res = self.res.append(row_df)
        if self.res.shape[0] % flush_period == 0:
            self.flush()

    def flush(self, index=False):
        """Flushs current results to file and clear buffer.
        """
        self.res.to_csv(self.csv, index=index, mode='a',
            header=False, columns=self.columns)
        print(f'{self.res.shape[0]} lines flushed to {self.csv}.')
        self.res = self.res[0:0]
    
    def read(self, idx_col=False):
        """Reads the DataFrame from csv. Redundant for now, but can be kept
        to ensure future consistency with our result format. 
        """
        self.res = pd.read_csv(self.csv, index_col=idx_col)
        return self.res
    
