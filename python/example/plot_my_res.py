from my_flows_result import FlowsResult
import pandas as pd
import matplotlib
from matplotlib import pyplot as plt

csv = 'my_aimd_result.csv'
fres = FlowsResult(csv)
data = fres.read()
# ax = fres.res.plot(x = 'tid', y = ['cwnd', 'sacked', 'loss', 'rtt'])
fig, axs = plt.subplots(2,2)
fres.res.plot(ax=axs[0,0], x = 'tid', y = ['cwnd'])
fres.res.plot(ax=axs[0,1], x = 'tid', y = ['rtt'])
fres.res.plot(ax=axs[1,0], x = 'tid', y = ['loss'])
fres.res.plot(ax=axs[1,1], x = 'tid', y = ['sacked'])
plt.tight_layout()
plt.show()


