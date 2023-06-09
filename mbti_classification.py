# -*- coding: utf-8 -*-
"""mbti.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/19VfBLQ2UnzXiUVRXRvm2lF4nRAODTgEq
"""

!pip install transformers

!pip install datasets

import tensorflow as tf
from transformers import AutoTokenizer,TFBertModel, TFAutoModelForSequenceClassification
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
import nltk
import re
import seaborn as sns

device_name = tf.test.gpu_device_name()
if device_name != '/device:GPU:0':
  raise SystemError('GPU device not found')
print('Found GPU at: {}'.format(device_name))

dataset= pd.read_csv("mbti_1.csv")
dataset.head(5)

labels=dataset["type"].unique()
a=dataset.groupby("type")

keys=[]
counts=[]
for i in a:
    keys.append(i[0])
    counts.append(len(i[1]))
counts
a=pd.DataFrame({"keys":keys, "count":counts})
print(a)

all={"I":0, "E":0, "N":0,"S":0, "T":0, "F":0, "J":0,"P":0} 

for i in dataset["type"]:
    for j in i:
        all[j]+=1

print(all)

pair1_labels = ['I', 'N', 'T', 'J']
class1_values = [all[i] for i in pair1_labels]
pair2_labels = ['E', 'S', 'F', 'P']
class2_values = [all[i] for i in pair2_labels]
x_ticks= ['I-E', 'N-S', 'T-F', 'J-P' ]
bar_width = 0.35
colors = ['blue', 'orange', 'green', 'red']

r1 = range(len(x_ticks))
r2 = [x + bar_width for x in r1]

# Define different colors and hatch patterns for each pair
colors = ['blue', 'orange', 'green', 'red']  # Example colors
hatches = ['//', '\\', 'x', 'o']  # Example hatch patterns

# Plot the bars with different colors and hatch patterns
for i, (val1, val2) in enumerate(zip(class1_values, class2_values)):
    plt.bar(r1[i], val1, color='turquoise', hatch=hatches[i], width=bar_width, edgecolor='white', label=pair1_labels[i])
    plt.bar(r2[i], val2, color='magenta', hatch=hatches[i], width=bar_width, edgecolor='white', label=pair2_labels[i])

# Add x-tick labels
plt.xticks([r + bar_width/2 for r in range(len(x_ticks))], x_ticks)
plt.xlabel('Personality Classes')
plt.ylabel('Counts')
plt.title('Bar Chart Personalty pairs')

# plt.legend()
plt.show()

sns.barplot(data=a, x="keys", y="count")
axes = ["I-E","N-S","T-F","J-P"]
classes = {"I":0, "E":1, 
           "N":0,"S":1, 
           "T":0, "F":1, 
           "J":0,"P":1}

def text_preprocessing(text):
    
    text = text.lower()
    text = re.sub('\[.*?\]', '', text)
    text = re.sub('https?://\S+|www\.\S+', '', text)
    text = re.sub('<.*?>+', '', text)
    text = re.sub('\n', '', text)
    text = re.sub('\w*\d\w*', '', text)
    text.encode('ascii', 'ignore').decode('ascii')
    if text.startswith("'"):
        text = text[1:-1]
    
    return text

def tokenization_function(text, label):
    print(text)
    tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
    encodings = tokenizer(text, truncation=True, padding='max_length', max_length=max_len, return_tensors='tf')
    input_ids = encodings['input_ids']
    attention_mask = encodings['attention_mask']
    return {'input_ids': input_ids, 'attention_mask': attention_mask}, label

data = dataset.sample(frac=1)
labels = []
for pers_string in data["type"]:
    pers_vector = []
    for char in pers_string:
        pers_vector.append(classes[char])
    labels.append(pers_vector)
print(labels)

train_size=6624
val_size=1024
test_size=1024
sentences = dataset["posts"].apply(str).apply(lambda x: text_preprocessing(x))
labels = np.array(labels, dtype="float32")
train_sentences = sentences[:train_size]
y_train = labels[:train_size]
val_sentences = sentences[train_size:train_size+val_size]
y_val = labels[train_size:train_size+val_size]
test_sentences = sentences[train_size+val_size:train_size+val_size+test_size]
y_test = labels[train_size+val_size:train_size+val_size+test_size]

model_checkpoint = "bert-base-uncased"



y_train = tf.convert_to_tensor(y_train)
y_val = tf.convert_to_tensor(y_val)
y_test = tf.convert_to_tensor(y_test)

dataset_train = tf.data.Dataset.from_tensor_slices((train_sentences, y_train))
dataset_train = dataset_train.map(tokenization_function).shuffle(100).batch(8)

dataset_val = tf.data.Dataset.from_tensor_slices((val_sentences, y_val))
dataset_val = dataset_val.map(tokenization_function).batch(8)

dataset_test = tf.data.Dataset.from_tensor_slices((test_sentences, y_test))
dataset_test = dataset_test.map(tokenization_function).batch(8)

type(dataset_train)

num_labels=4
model = TFAutoModelForSequenceClassification.from_pretrained(
    model_checkpoint, num_labels=num_labels, 
)

from transformers import create_optimizer
from tensorflow.keras.callbacks import ModelCheckpoint
import keras
num_epochs = 7


optimizer = tf.keras.optimizers.Adam(learning_rate=2e-5)
loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
metrics = ['accuracy']
model.compile(optimizer='adam', loss=loss, metrics=['accuracy'])

model.fit(
    dataset_train,
    validation_data=dataset_val,
    epochs=10,
    batch_size=8,
)

test_results = model.evaluate(dataset_test)
print("Test Loss:", test_results[0])
print("Test Accuracy:", test_results[1])