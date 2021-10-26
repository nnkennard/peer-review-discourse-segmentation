import collections
import glob
import json


class Segment(object):

  def __init__(self, label, start, excl_end):
    self.label = label
    self.start = start
    self.excl_end = excl_end

  def __repr__(self):
    return "({0} s={1} e={2})".format(self.label, self.start, self.excl_end)


SUBSETS = "train dev test".split()


def review_label_segmentation(pair, label):
  sequence = [sentence[label] for sentence in pair["review_sentences"]]
  segments = []
  while True:
    curr = sequence.pop(0)
    if segments and curr == segments[-1].label:
      segments[-1].excl_end += 1
    else:
      if segments:
        i = segments[-1].excl_end
      else:
        i = 0
      segments.append(Segment(curr, i, i + 1))
    if not sequence:
      break
  return segments


def review_alignment_segmentation(pair):
  num_review_sentences = len(pair["review_sentences"])
  mappers = {i: set([]) for i in range(num_review_sentences)}
  alignments = [x["alignment"] for x in pair["rebuttal_sentences"]]
  for i, alignment in enumerate(alignments):
    _, indices = alignment
    if indices is not None:
      for j in indices:
        mappers[j].add(i)

  i = 0
  segments = []
  must_start_new_segment = False
  while i < num_review_sentences:
    if must_start_new_segment:
      if mappers[i]:
        segments.append(Segment("temp_name", i, i + 1))
        must_start_new_segment = False
    else:
      if not mappers[i]:
        pass
      else:
        if mappers[i].intersection(mappers[i - 1]):
          segments[-1].excl_end += 1
        else:
          segments.append(Segment("temp_name", i, i + 1))
        must_start_new_segment = False
    i += 1

  for segment in segments:
    alignment_starter = mappers[segment.start]
    for index in range(segment.start + 1, segment.excl_end):
      alignment_starter = alignment_starter.intersection(mappers[index])
    segment.label = "reb_idxs_" + "|".join(
        [str(i) for i in sorted(alignment_starter)])

  return segments


def get_datasets():
  dataset_dir = "final_dataset/"

  datasets = collections.defaultdict(list)

  for subset in SUBSETS:
    for filename in glob.glob(dataset_dir + subset + "/*"):
      with open(filename, 'r') as f:
        datasets[subset].append(json.load(f))

  return datasets


def main():

  datasets = get_datasets()
  all_pairs = sum(datasets.values(), [])

  for pair in all_pairs:
    print(review_label_segmentation(pair, "coarse"))
    print(review_alignment_segmentation(pair))
    exit()

  pass


if __name__ == "__main__":
  main()
