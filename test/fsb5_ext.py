
import fsb5

with open("icechime.fsb", "rb") as f:
    fsb = fsb5.FSB5(f.read())


print(fsb.header)

# get the extension of samples based off the sound format specified in the header
ext = fsb.get_sample_extension()

# iterate over samples
for sample in fsb.samples:
  # print sample properties
  print('''\t{sample.name}.{extension}:
  Frequency: {sample.frequency}
  Channels: {sample.channels}
  Samples: {sample.samples}'''.format(sample=sample, extension=ext))

  # rebuild the sample and save
  with open('{0}.{1}'.format(sample.name, ext), 'wb') as f:
    rebuilt_sample = fsb.rebuild_sample(sample)
    f.write(rebuilt_sample)

    