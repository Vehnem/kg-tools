from openie import StanfordOpenIE
import sys
# https://stanfordnlp.github.io/CoreNLP/openie.html#api
# Default value of openie.affinity_probability_cap was 1/3.
properties = {
    'openie.affinity_probability_cap': 2 / 3,
}
if len(sys.argv) > 1:
    input = sys.argv[1]

with StanfordOpenIE(properties=properties) as client:
    text = 'Barack Obama was born in Hawaii. Richard Manning wrote this sentence.'
    print('Text: %s.' % input)
    for triple in client.annotate(input):
        print('|-', triple)
