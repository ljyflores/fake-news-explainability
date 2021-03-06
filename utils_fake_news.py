# -*- coding: utf-8 -*-
"""encoder.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/16U1z0eTNULPOF-3ZXPHjDps1VImiVYDm
"""

import pandas as pd
import numpy as np
import json, re
from tqdm import tqdm_notebook
from uuid import uuid4
import time
import datetime
import random
import itertools

## Torch Modules
import torch
import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from torch.utils.data import (
    Dataset, 
    DataLoader,
    TensorDataset, 
    random_split, 
    RandomSampler, 
    SequentialSampler)

# Transformers
from transformers import (
    BertForSequenceClassification,
    BertTokenizer,
    RobertaForSequenceClassification,
    RobertaTokenizer,
    AdamW,
    get_linear_schedule_with_warmup)

# BERT
bert_tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

# Encoder Functions
def encode_dataframe(statement_col, target_col, unpack=False):
    # Tokenize statements
    bert_encoded_dict = statement_col.apply(lambda sent: bert_tokenizer.encode_plus(
                                      sent,                      # Sentence to encode.
                                      add_special_tokens = True, # Add '[CLS]' and '[SEP]'
                                      max_length = 120,           # Pad & truncate all sentences.
                                      pad_to_max_length = True,
                                      return_attention_mask = True,   # Construct attn. masks.
                                      return_tensors = 'pt',     # Return pytorch tensors.
                                      truncation = True
                                ))
    bert_input_ids = torch.cat([item['input_ids'] for item in bert_encoded_dict], dim=0)
    bert_attention_masks = torch.cat([item['attention_mask'] for item in bert_encoded_dict], dim=0)

    # Format targets
    labels = torch.tensor(target_col)
    sentence_ids = torch.tensor(range(len(target_col)))

    # Combine the training inputs into a TensorDataset
    bert_dataset = TensorDataset(sentence_ids, bert_input_ids, bert_attention_masks, labels)

    # Remove indices
    trial_dataset =  index_remover(bert_dataset)

    if unpack:
        return bert_input_ids, bert_attention_masks, labels
    else:
        return trial_dataset

def index_remover(tensordata):
    input_ids = []
    attention_masks = []
    labels = []
   
    for a,b,c,d in tensordata:
        input_ids.append(b.tolist())
        attention_masks.append(c.tolist())
        labels.append(d.tolist())
        
    input_ids = torch.tensor(input_ids)
    attention_masks = torch.tensor(attention_masks)
    labels = torch.tensor(labels)
    
    final_dataset =  TensorDataset(input_ids, attention_masks, labels)
    return final_dataset

# Labeling Data
# Target labels
label_encodings2 = {
    'barely-true':1, 
    'false':1, 
    'half-true':1, 
    'mostly-true':0, 
    'pants-fire':0, 
    'true':0
}

# Accuracy/Reporting Functions
# Function to calculate the accuracy of our predictions vs labels
def flat_accuracy(preds, labels):
    pred_flat = np.argmax(preds, axis=1).flatten()
    labels_flat = labels.flatten()
    return np.sum(pred_flat == labels_flat) / len(labels_flat)

def format_time(elapsed):
    '''
    Takes a time in seconds and returns a string hh:mm:ss
    '''
    # Round to the nearest second.
    elapsed_rounded = int(round((elapsed)))
    
    # Format as hh:mm:ss
    return str(datetime.timedelta(seconds=elapsed_rounded))