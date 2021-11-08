import json
import os

import segment_lib

class Filetypes(object):
  INPUT = "input"
  OUTPUT = "output"
  CONST = "const"
  DEP = "dep"
  GRID = "grid"
  ALL = [INPUT, OUTPUT, CONST, DEP, GRID]


def get_filenames(review_id, temp_dir):
  os.makedirs(temp_dir, exist_ok=True)
  return {
    filetype: "{0}/{1}_{2}.txt".format(temp_dir, filetype, review_id)
      for filetype in Filetypes.ALL
      }


def update_noun_types(dep_type, np_words, curr_nouns_type):
    for word in np_words:
        if word not in curr_nouns_type:
            curr_nouns_type[word] = dep_type
        if curr_nouns_type[word] == "x" or curr_nouns_type[word] == "o":
            curr_nouns_type[word] = dep_type
    return curr_nouns_type


def get_np(dependency, const_parse):
    target_id = dependency['dependent']
    index = 0
    nouns = []
    for line in const_parse.splitlines():
        if ")" not in line:
            continue
        tokens = line.strip().split(") (")
        num_tokens = len(tokens)  # remove phrase label
        phrase_start_idx = index + 1
        index += num_tokens
        phrase_end_idx = index + 1
        if target_id <= index and tokens[0].startswith("(NP"):
            for token in tokens:
                if token.startswith("(NP"):
                    token = token[3:].strip()
                while token.startswith("("):
                    token = token[1:] 
                while token.endswith(")"):
                    token = token[:-1].strip()
                word = token.split(None, 1)[1]  # remove POS tag
                if token.startswith("NN"):
                    nouns.append(word.lower())
                elif token.startswith("PRP "):
                    nouns.append(word.lower())
                elif token.startswith("DT") and len(tokens) == 1:
                    nouns.append(word.lower())  # is noun phrase, only one DT word (this, all) in the phrase
            break
    return nouns, phrase_start_idx, phrase_end_idx



def run(sentences, review_id, pipeline):
  filenames = get_filenames(review_id, "./eg_temp/")

  with open(filenames[Filetypes.INPUT], 'w') as f:
    f.write("\n".join([x["text"] for x in sentences]) + "\n")

  with open(filenames[Filetypes.INPUT], 'r') as in_file:
    nouns_list = []
    nouns_dict = {}
    sent_annotations = []
    const_out = open(filenames[Filetypes.CONST], "w")
    dep_out = open(filenames[Filetypes.DEP], "w")
    grid_out = open(filenames[Filetypes.GRID], "w")
    # read text document
    document_lines = []
    document = in_file.read()
    try:
      output = pipeline.annotate(
          document,
          properties={
              'annotators': 'tokenize,ssplit,pos,depparse,parse',
              'outputFormat': 'json',
              'ssplit.eolonly': True,
              'timeout': '50000',
          })
    except:
      print('Failed to parse file %s' % filenames[Filetypes.INPUT])
      return None
    if output == 'CoreNLP request timed out. Your document may be too long.':
      print('Timed out when attempting to parse file %s' % filename)
      return None
    if output == "Could not handle incoming annotation":
      return None
    output = json.loads(output)
    for sent in output['sentences']:
      sent_idx = sent['index'] + 1
      const_out.write(sent['parse'] + "\n")
      json.dump(sent['basicDependencies'], dep_out)
      dep_out.write("\n")
      curr_nouns_type = {}
      for token in sent['tokens']:
        # collect all nouns and pronouns
        if token['pos'].startswith("NN") or token['pos'] == 'PRP':
          token_str = token['word'].lower()
          curr_nouns_type[token_str] = "x"
          if token_str not in nouns_dict:
            nouns_list.append(token_str)
            nouns_dict[token_str] = 0
          nouns_dict[token_str] += 1
      # find highest-ranked role of entity in this sentence (subj > obj > other)
      for dep in sent['basicDependencies']:
        dep_type = ""
        if dep['dep'] == 'nsubj' or dep['dep'] == 'nsubjpass':
          dep_type = "s"
        elif dep['dep'] == 'dobj':
          dep_type = "o"
        if dep_type != "":
          np, phrase_start_idx, phrase_end_idx = get_np(dep, sent['parse'])
          curr_nouns_type = update_noun_types(dep_type, np, curr_nouns_type)
      sent_annotations.append(curr_nouns_type)

    # output entity grid
    for noun in nouns_list:
      grid_out.write(noun + " ")
      for sent_ann in sent_annotations:
        if noun in sent_ann:
          grid_out.write(sent_ann[noun] + " ")
        else:
          grid_out.write("- ")
      grid_out.write(str(nouns_dict[noun]) +
                     "\n")  # entity frequency (salience count)
    grid_out.close()
    const_out.close()
    dep_out.close()

    return convert_grid_to_segments(filenames[Filetypes.GRID])
    
def convert_grid_to_segments(grid_filename):
  segments = []
  with open(grid_filename, 'r') as f:
    for line in f:
      fields = line.split()
      _ = fields.pop(-1)
      entity = fields.pop(0)
      first = None
      last = None
      for i, item in enumerate(fields):
        if item == "-":
          continue
        else:
          first = i
          break
      for i, item in enumerate(reversed(fields)):
        if item == "-":
          continue
        else:
          last = len(fields) - i - 1
          break

      if first is not None and last is not None and not first == last:
        segments.append(segment_lib.Segment(entity, first, last))

  return segment_lib.jsonify_segments(segments)

