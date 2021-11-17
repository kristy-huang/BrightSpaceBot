import spacy


nlp = spacy.load('en_core_web_md')

s11 = nlp("Update notification schedule")
s12 = nlp("Update class schedule")
s13 = nlp("Update download schedule")

s2 = nlp("please update my notificaion schedule")

print(s11.similarity(s2))
print(s12.similarity(s2))
print(s13.similarity(s2))