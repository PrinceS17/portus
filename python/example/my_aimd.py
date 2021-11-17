import sys
import pyportus as portus
import math
import pandas as pd
from my_flows_result import FlowsResult
from enum import Enum

"""
Current flaws:
    1. No slow start, may cause severe underusing;
    2. interrupt not captured to flush in the end.
"""

class State(Enum):
    SS = 0
    CA = 1


aimd_result = FlowsResult('my_aimd_result.csv', clear=True)

class AIMDFlow():
    INIT_CWND = 10
    # formula: 
    #   alpha = a
    #   beta = 1 - 2a / (a + 3)
    # ALPHA = 0.5
    # BETA = 0.72
    ALPHA, BETA = 1, 0.5        # for test
    ID = 0

    def __init__(self, datapath, datapath_info):
        self.datapath = datapath
        self.datapath_info = datapath_info
        self.id = AIMDFlow.ID
        AIMDFlow.ID += 1
        self.init_cwnd = float(self.datapath_info.mss * AIMDFlow.INIT_CWND)
        self.cwnd = self.init_cwnd
        self.alpha, self.beta = AIMDFlow.ALPHA, AIMDFlow.BETA
        self.datapath.set_program("default", [("Cwnd", int(self.cwnd))])
        self.n_line = 0
        self.state = State.SS
        self.ssthreth = 64000

    def on_report(self, r):
        # very draft implementation of reno...
        loss_condition = r.loss > 0 or r.sacked > 0
        if self.state == State.SS:
            if not loss_condition:
                self.virt_cwnd = self.cwnd + r.acked
                if self.virt_cwnd >= self.ssthreth:
                    ai_part = (r.acked - (self.ssthreth - self.cwnd)) / self.ssthreth
                    self.cwnd = self.ssthreth + self.alpha * self.datapath_info.mss * ai_part
                    self.state = State.CA
                    print(' Smooth ends Slow Start!')
                else:
                    self.cwnd = self.virt_cwnd
            elif not r.timeout:
                self.cwnd *= self.beta
                self.ssthreth = self.cwnd
                self.state = State.CA
                print(' Loss ends Slow Start!')
            else:
                self.cwnd = self.init_cwnd
                self.state = State.SS
                print(' Timeout restarts Slow Start!')
        else:
            if not loss_condition:
                self.cwnd += self.alpha * self.datapath_info.mss * (r.acked / self.cwnd)
            elif not r.timeout:
                self.cwnd *= self.beta
                # TODO: ssthresh update or not?
            else:
                self.cwnd = self.init_cwnd
                self.state = State.SS
        
        self.cwnd, self.ssthreth = math.floor(self.cwnd), math.floor(self.ssthreth)
        self.cwnd = max(self.cwnd, self.init_cwnd)
        self.datapath.update_field("Cwnd", int(self.cwnd))

        # export result
        print(f"cwnd {int(self.cwnd)} loss {r.loss} sacked {r.sacked} acked {r.acked} rtt {r.rtt} inflight {r.inflight}")
        aimd_result.append([[self.id, self.n_line, self.cwnd, 0, r.loss, r.sacked, r.acked, r.rtt, r.inflight]])
        self.n_line += 1            # placeholder for time t

class AIMD(portus.AlgBase):
    def datapath_programs(self):
        return {
                "default" : """\
                (def (Report
                    (volatile acked 0)
                    (volatile sacked 0)
                    (volatile loss 0)
                    (volatile timeout false)
                    (volatile rtt 0)
                    (volatile inflight 0)
                ))
                (when true
                    (:= Report.inflight Flow.packets_in_flight)
                    (:= Report.rtt Flow.rtt_sample_us)
                    (:= Report.acked (+ Report.acked Ack.bytes_acked))
                    (:= Report.sacked (+ Report.sacked Ack.packets_misordered))
                    (:= Report.loss Ack.lost_pkts_sample)
                    (:= Report.timeout Flow.was_timeout)
                    (fallthrough)
                )
                (when (|| Report.timeout (> Report.loss 0))
                    (report)
                    (:= Micros 0)
                )
                (when (> Micros Flow.rtt_sample_us)
                    (report)
                    (:= Micros 0)
                )
            """
        }

    def new_flow(self, datapath, datapath_info):
        return AIMDFlow(datapath, datapath_info)

alg = AIMD()


if __name__ == '__main__':
    try:
        portus.start("netlink", alg)
    except KeyboardInterrupt:
        aimd_result.flush()
