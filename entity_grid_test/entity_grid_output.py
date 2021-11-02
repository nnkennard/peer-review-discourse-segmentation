import pandas as pd
import glob
import os


def main():
  if not os.path.exists('output/'):
    os.makedirs('output/')

  text_dir = 'text/'
  grid_dir = 'grid/'
  output_dir = 'output/'
  for filename in glob.glob(text_dir + "/*"):
    output_csv = pd.DataFrame()
    with open(filename, 'r') as f:
      output_csv['rr_sentences'] = f.readlines()

    grid_filename = grid_dir + filename[-14:]
    with open(grid_filename, 'r') as f:
      for line in f.readlines():
        line_list = line.split(' ')
        word = line_list[0]
        output_csv[word] = line_list[1:-1]
    output_csv.to_csv(output_dir + filename[-14:-4] + '.csv')


if __name__ == "__main__":
  main()
