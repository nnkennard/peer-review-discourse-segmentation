import collections
import glob
import json
import nltk
from nltk.corpus import brown


class Segment(object):

  def __init__(self, label, start, excl_end):
    self.label = label
    self.start = start
    self.excl_end = excl_end

  def __repr__(self):
    return "({0} s={1} e={2})".format(self.label, self.start, self.excl_end)


SUBSETS = "train dev test".split()

class Baseline(object):
  label = "label"
  alignment = "alignment"
  text_tiling = "text_tiling"




def review_label_segmentation(pair, label):
  sequence = [sentence["coarse"] for sentence in pair["review_sentences"]]
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
  mappers = {i: set([]) for i in range(num_review_sentences + 15)}
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


def get_text_block(sentences):
  return " ".join([x["text"] + x["suffix"] for x in sentences])


def condense_strings(string):
  return "".join(string.split())

def run_texttiling(sentences, tt):
  text_block = get_text_block(sentences)
  sentence_list = [x["text"] for x in sentences]
  tt_segments = tt.tokenize(text_block)
  matched_segment_start = 0
  matched_segment_end = 0
  segments = []
  for segment in tt_segments:
    condensed_segment = condense_strings(segment)
    while True:
      matched_segment = condense_strings(" ".join(
        sentence_list[matched_segment_start:matched_segment_end]))
      if matched_segment == condensed_segment:
        index = len(segments)
        segments.append(Segment("tt_segment_{0}".format(index), matched_segment_start,
        matched_segment_end))
        matched_segment_start = matched_segment_end
        break
      else:
        matched_segment_end += 1

  return segments


def texttiling_segmentation(pair, tt):
  return (run_texttiling(pair["review_sentences"], tt),
  run_texttiling(pair["rebuttal_sentences"], tt))
  

def get_datasets():
  dataset_dir = "../peer-review-discourse-dataset/data_prep/dsds/final_dataset/"

  datasets = collections.defaultdict(list)

  for subset in SUBSETS:
    for filename in glob.glob(dataset_dir + subset + "/*"):
      with open(filename, 'r') as f:
        datasets[subset].append(json.load(f))

  return datasets


def main():

  datasets = get_datasets()
  all_pairs = sum(datasets.values(), [])

  tt = nltk.TextTilingTokenizer()

  for pair in all_pairs[:10]:
    review_tt_segments, rebuttal_tt_segments = texttiling_segmentation(pair, tt)
    review_segmentations = {
      Baseline.label: review_label_segmentation(pair),
      Baseline.alignment: review_alignment_segmentation(pair),
      Baseline.text_tiling: review_tt_segments,
    }
    rebuttal_segmentations = {
      Baseline.text_tiling: rebuttal_tt_segments,
    }




if __name__ == "__main__":
  main()
