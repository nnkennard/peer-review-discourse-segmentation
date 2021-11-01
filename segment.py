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

  def to_dict(self):
    return {
      "label": self.label,
      "start": self.start,
      "excl_end": self.excl_end
    }

  def __repr__(self):
    return "({0} s={1} e={2})".format(self.label, self.start, self.excl_end)


SUBSETS = "train dev test".split()

class Baseline(object):
  label = "label"
  alignment = "alignment"
  text_tiling = "text_tiling"


def segment_label_list(sequence):
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
  return jsonify_segments(segments)

def rebuttal_label_segmentation(pair):
  return segment_label_list(
  [sentence["fine"] for sentence in pair["rebuttal_sentences"]])


def review_label_segmentation(pair):
  sequence = []
  for sentence in pair["review_sentences"]:
    if sentence["fine"] == 'none':
      sequence.append(sentence["coarse"])
    else:
      sequence.append(sentence["coarse"] + "|" + sentence["fine"].split("_")[1])
  return segment_label_list(sequence)


def segment_alignment_map(alignment_map, final_sequence_len, name_prefix):
  i = 0
  segments = []
  must_start_new_segment = False
  while i < final_sequence_len:
    if must_start_new_segment:
      if alignment_map[i]:
        segments.append(Segment("temp_name", i, i + 1))
        must_start_new_segment = False
    else:
      if not alignment_map[i]:
        pass
      else:
        if alignment_map[i].intersection(alignment_map[i - 1]):
          segments[-1].excl_end += 1
        else:
          segments.append(Segment("temp_name", i, i + 1))
        must_start_new_segment = False
    i += 1

  for segment in segments:
    alignment_starter = alignment_map[segment.start]
    for index in range(segment.start + 1, segment.excl_end):
      alignment_starter = alignment_starter.intersection(alignment_map[index])
    segment.label = name_prefix + "|".join(
        [str(i) for i in sorted(alignment_starter)])
  return jsonify_segments(segments)


def rebuttal_alignment_segmentation(pair):
  num_rebuttal_sentences = len(pair["rebuttal_sentences"])
  mappers = {i: set([]) for i in range(num_rebuttal_sentences)}
  for i, reb_sentence in enumerate(pair["rebuttal_sentences"]):
    _, indices = reb_sentence["alignment"]
    if indices is not None:
      mappers[i] = set(indices)
  return segment_alignment_map(mappers, num_rebuttal_sentences, "rev_idxs_")

def review_alignment_segmentation(pair):
  num_review_sentences = len(pair["review_sentences"])
  mappers = {i: set([]) for i in range(num_review_sentences + 15)}
  alignments = [x["alignment"] for x in pair["rebuttal_sentences"]]
  for i, alignment in enumerate(alignments):
    _, indices = alignment
    if indices is not None:
      for j in indices:
        mappers[j].add(i)
  return segment_alignment_map(mappers, num_review_sentences, "reb_idxs_")


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

  return jsonify_segments(segments)

def jsonify_segments(segments):
  return [x.to_dict() for x in segments]

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

  all_segmentations = []

  for pair in datasets['train'][:10]:
    review_tt_segments, rebuttal_tt_segments = texttiling_segmentation(pair, tt)
    review_segmentations = {
      Baseline.label: review_label_segmentation(pair),
      Baseline.alignment: review_alignment_segmentation(pair),
      Baseline.text_tiling: review_tt_segments,
    }
    rebuttal_segmentations = {
      Baseline.text_tiling: rebuttal_tt_segments,
      Baseline.label: rebuttal_label_segmentation(pair),
      Baseline.alignment: rebuttal_alignment_segmentation(pair),
    }
    all_segmentations.append({
    "review_id": pair["metadata"]["review_id"],
    "review_sentences": [x["text"] + x["suffix"]
          for x in pair["review_sentences"]],
    "rebuttal_sentences": [x["text"] + x["suffix"]
          for x in pair["rebuttal_sentences"]],
    "review_segmentations": review_segmentations,
    "rebuttal_segmentations": rebuttal_segmentations})

  with open('baselines.json', 'w') as f:
    json.dump(all_segmentations, f)


if __name__ == "__main__":
  main()
