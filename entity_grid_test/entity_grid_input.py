import collections
import glob
import json
import sys
import os

SUBSETS = "train dev test".split()

def get_text_block(sentences):
  return " ".join([x["text"] + '\n' for x in sentences])

def get_datasets():
  dataset_dir = "../../peer-review-discourse-dataset/data_prep/final_dataset/"

  datasets = collections.defaultdict(list)

  for subset in SUBSETS:
    for filename in glob.glob(dataset_dir + subset + "/*"):
      with open(filename, 'r') as f:
        datasets[subset].append(json.load(f))

  return datasets


def main():
  datasets = get_datasets()

  if not os.path.exists('text/'):
    os.makedirs('text/')

  text_dir = 'text/'
  for pair in datasets['train'][:10]:
    filename = pair['metadata']['review_id'] + '.txt'
    text_block = get_text_block(pair['review_sentences'])
    out_file = open(text_dir + filename, 'w')
    print(text_dir, filename)
    print(pair["metadata"])
    out_file.write(text_block)
    out_file.close()

if __name__ == "__main__":
  main()
