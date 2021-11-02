import collections
import glob
import json
import random

INDIVIDUAL_CARD_PAIR_TEMPLATE = """
 <h2 class="title is-2"> %%REVIEW_INFO%% </h2>
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
      <title> Review-rebuttal segmentation viewer </title>
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

def use_label_check(seg_type):
  return 'label' in seg_type

def get_segment_sequences(num_sentences, segmentations):
  segment_sequences = {}
  for segmentation_type, segments in segmentations.items():
    use_label = use_label_check(segmentation_type)
    labels = [""] * num_sentences
    for i, segment in enumerate(segments):
      if use_label:
        h_type = segment["label"].split("_")[1]
      else:
        h_type = type_getter[i %2]
      for j in range(segment["start"], segment["excl_end"]):
        labels[j] = h_type
    segment_sequences[segmentation_type] = labels
  return segment_sequences

def get_row(sentence, labels):
  row_string = '<tr><td>' + sentence.replace("\n", "<br><br>") + "</td>"
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

  card_content = "".join([
    '<table class="table">',
    '<thead> <td> Sentence </td>',
    " ".join(['<td>' + model + '</td>' for model in models])
    ,"</thead>", rows, "</table>"
    ])
  #return INDIVIDUAL_CARD_PAIR_TEMPLATE.replace("%%REVIEW_CONTENT%%",
  #card_content)
  return card_content



def main():

  with open("baselines.json", 'r') as f:
    examples = json.load(f)


  html_text = ""
  for example in examples:

    card_text = ""
  
    #review_info = '<h1 class="is-h1"> Segmentations for ' + example["review_id"] +"</h1>"
    review_info = 'Segmentations for ' + example["review_id"]

    card_text +=  '<h3 class="title is-3"> Review </h3>'
    card_text += get_html_table(example["review_sentences"], example["review_segmentations"])
    card_text +=  '<h3 class="title is-3"> Rebuttal </h3>'
    card_text += "Rebuttal <br>" 
    card_text += get_html_table(example["rebuttal_sentences"], example["rebuttal_segmentations"])

    html_text += INDIVIDUAL_CARD_PAIR_TEMPLATE.replace("%%REVIEW_INFO%%",
    review_info).replace("%%REVIEW_CONTENT%%", card_text)

  print(HTML_STARTER + html_text + HTML_ENDER)


if __name__ == "__main__":
  main()
