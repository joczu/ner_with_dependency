# 
# @author: Allan
#

import torch.nn as nn
import torch.nn.functional as F



class GCN(nn.Module):
    def __init__(self, config):
        super().__init__()

        self.gcn_hidden_dim = config.dep_hidden_dim
        self.num_gcn_layers = config.num_gcn_layers
        self.gcn_mlp_layers = config.gcn_mlp_layers
        # gcn layer
        self.layers = self.num_gcn_layers
        self.device = config.device
        self.mem_dim = self.gcn_hidden_dim
        # self.in_dim = config.hidden_dim + config.dep_emb_size  ## lstm hidden dim
        self.in_dim = config.hidden_dim  ## lstm hidden dim

        self.gcn_drop = nn.Dropout(config.gcn_dropout).to(self.device)

        # gcn layer
        self.W = nn.ModuleList()

        for layer in range(self.layers):
            input_dim = self.in_dim if layer == 0 else self.mem_dim
            self.W.append(nn.Linear(input_dim, self.mem_dim).to(self.device))

        # output mlp layers
        in_dim = config.hidden_dim
        layers = [nn.Linear(in_dim, self.gcn_hidden_dim).to(self.device), nn.ReLU().to(self.device)]
        for _ in range(self.gcn_mlp_layers - 1):
            layers += [nn.Linear(self.gcn_hidden_dim, self.gcn_hidden_dim).to(self.device), nn.ReLU().to(self.device)]

        self.out_mlp = nn.Sequential(*layers).to(self.device)



    def forward(self, gcn_inputs, word_seq_len, adj_matrix):

        # print(adj_matrix.size())

        denom = adj_matrix.sum(2).unsqueeze(2) + 1

        for l in range(self.layers):
            Ax = adj_matrix.bmm(gcn_inputs)
            AxW = self.W[l](Ax)
            AxW = AxW + self.W[l](gcn_inputs)  # self loop
            AxW = AxW / denom

            gAxW = F.relu(AxW)
            gcn_inputs = self.gcn_drop(gAxW) if l < self.layers - 1 else gAxW


        outputs = self.out_mlp(gcn_inputs)
        return outputs


