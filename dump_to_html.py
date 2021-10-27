import collections
import glob
import json
import random

INDIVIDUAL_CARD_PAIR_TEMPLATE = """
 <h1 class="subtitle"> %%REVIEW_INFO%% </h1>
 <div class="columns">
    <div class="column">
       <div class="card">
          <div class="card-content">
             <div class="content">
                %%REVIEW_CONTENT%%
             </div>
          </div>
       </div>
    </div>
 </div>
"""

HTML_STARTER = """
<HTML>
   <head>
      <title> Review-rebuttal alignment viewer </title>
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.3/css/bulma-rtl.min.css">
   </head>
   <body>
 <div class="container">
"""

HTML_ENDER = """
</div>
   </body>
</HTML>
"""

  
type_getter = ["*", "@"]

def get_segment_sequences(num_sentences, segmentations):
  segment_sequences = {}
  for segmentation_type, segments in segmentations.items():
    labels = [""] * num_sentences
    for i, segment in enumerate(segments):
      h_type = type_getter[i %2]
      for j in range(segment["start"], segment["excl_end"]):
        labels[j] = h_type
    segment_sequences[segmentation_type] = labels
  return segment_sequences

def get_row(sentence, labels):
  row_string = '<tr><td>' + sentence.replace("\n", "<mark>\\\\<br></mark>") + "</td>"
  for label in labels:
    row_string += '<td>' + label + '</td>'
  row_string += "</tr>"
  return row_string

def get_html_table(sentences, segmentations):
  segment_sequences = get_segment_sequences(len(sentences), segmentations)
  models = sorted(segmentations.keys())

  rows = ""  
  for i, sentence in enumerate(sentences):
    rows += "\n" + get_row(sentence, [segment_sequences[m][i] for m in models])

  return "".join([
    #HTML_STARTER,
    '<table class="table">',
    '<thead> <td> Sentence </td>',
    " ".join(['<td>' + model + '</td>' for model in models])
    ,"</thead>", rows, "</table>"
    #,HTML_ENDER
    ])



def main():

  with open("baselines.json", 'r') as f:
    examples = json.load(f)


  html_text = ""
  for example in examples:
    html_text += example["review_id"] + "<br/> Review <br>" 
    html_text += get_html_table(example["review_sentences"], example["review_segmentations"])
    html_text += "Rebuttal <br>" 
    html_text += get_html_table(example["rebuttal_sentences"], example["rebuttal_segmentations"])

  print(HTML_STARTER + html_text + HTML_ENDER)


if __name__ == "__main__":
  main()
