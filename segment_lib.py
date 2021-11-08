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


def jsonify_segments(segments):
  return [x.to_dict() for x in segments]


