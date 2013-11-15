import csv
from string import lower
from boilerpipe.extract import Extractor
import datetime
import gensim
from gensim.corpora import Dictionary
from goose import Goose
import nltk
from nltk.corpus import stopwords
import re
from pymongo import MongoClient

STOP_WORDS = "able,about,across,after,all,almost,also,am,among,an,and,any,are,as,at,be,because,been,but,by,can,cannot,could,dear,did,do,does,either,else,ever,every,for,from,get,got,had,has,have,he,her,hers,him,his,how,however,i,if,in,into,is,it,its,just,least,let,like,likely,may,me,might,most,must,my,neither,no,nor,not,of,off,often,on,only,or,other,our,own,rather,said,say,says,she,should,since,so,some,than,that,the,their,them,then,there,these,they,this,tis,to,too,twas,us,wants,was,we,were,what,when,where,which,while,who,whom,why,will,with,would,yet,you,your".split(",")

def get_boilerpipe_text(url):
    extractor = Extractor(extractor='ArticleExtractor', url=url)
    return extractor.getText()

# https://github.com/grangier/python-goose
def get_goose_text(url):
    extractor = Goose()
    article = extractor.extract(url=url)
    return article.cleaned_text

stopwords_eng = stopwords.words('english') + ['\'s', '\'d', '\'t', '\'re']
punctuation = ['.', ',', '!', '?', ':', '(', ')', ';', '-', '+', '[', ']', '&', '#', '<', '>', '*', '--']
bad_symbols = ['``', '\'\'', '"', '\'']
useless_words = ['also', 'would', 'say', 'says', 'many', 'new', 'could', 'last', 'first', 'n\'t']

def clean(text):
    # str = remove_nonalphanumeric(str)
    # str = collapse_whitespace(str)
    # str = remove_stop_words(str)
    # str = remove_single_words(str)
    sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
    sentences = sent_detector.tokenize(text)
    words = []
    for sentence in sentences:
        tokens = nltk.word_tokenize(sentence)
        tokens = map(lower, tokens)
        tokens = [t for t in tokens if
                  t not in stopwords_eng and
                  t not in punctuation and
                  t not in bad_symbols and
                  t not in useless_words]
        words.extend(tokens)

    return words

def remove_rare_words(db):
    all_words = {}
    articles = db.articles.find()
    for article in articles:
        for word in article['clean_text']:
            all_words.setdefault(word, 0)
            all_words[word] += 1
    words_once = [w for w in set(all_words.keys()) if all_words[w] == 1]
    print 'Found %s rare words' % len(words_once)
    i = 0
    articles = db.articles.find()
    for article in articles:
        print i
        i += 1
        words = article['clean_text']
        l = len(words)
        words = [w for w in words if w not in words_once]
        if len(words) < l:
            print 'Reduced text length by %s' % (l - len(words))
        db.articles.update({'_id': article['_id']}, {'$set': {
            'clean_text': words
        }})

def build_dictionary(db):
    dictionary = Dictionary()
    for article in db.articles.find():
        dictionary.doc2bow(article['clean_text'], allow_update=True)
    # print dictionary
    # dictionary.save('data/cnn.dict') # store the dictionary, for future reference
    return dictionary

def build_corpora(db):
    dictionary = Dictionary()
    corpus = []
    for article in db.articles.find():
        text = article['clean_text']
        dictionary.doc2bow(text, allow_update=True)
    dictionary.filter_extremes()
    for article in db.articles.find():
        text = article['clean_text']
        corpus.append(dictionary.doc2bow(text))
    gensim.corpora.MmCorpus.serialize('data/corpus.mm', corpus)
    dictionary.save('data/cnn.dict')
    return corpus, dictionary

def load_corpora():
    dictionary = Dictionary.load('data/cnn.dict')
    corpus = gensim.corpora.MmCorpus('data/corpus.mm')
    return corpus, dictionary

def load_news(file_name, db):
    with open(file_name, 'rb') as urls:
        file_reader = csv.reader(urls, delimiter=' ', quotechar='"')
        file_reader.next()
        idx = 0
        for row in file_reader:
            url = row[0]
            idx += 1
            cursor = db.articles.find({'url': url})
            if cursor.count():
                continue
            else:
                print 'Processing url[%s]: %s' % (idx, url)
                try:
                    text = get_goose_text(url)
                except Exception as e:
                    print 'Error happened %s' % e.message
                else:
                    print 'Saving extracted text'
                    article = {
                        'text': text,
                        'url': url,
                        'date': datetime.datetime.utcnow()
                    }
                    db.articles.insert(article)


# text = get_goose_text(url)
# print clean(text)
def clean_news(db):
    i = 0
    for article in db.articles.find():
        print 'Processing article %s (%s)' % (article['_id'], i)
        i += 1
        clean_text = clean(article['text'])
        db.articles.update({'_id': article['_id']}, {'$set': {
            'clean_text': clean_text
        }})
        if i < 10:
            print article['url']
            print clean_text



def __main__():
    client = MongoClient()
    db = client.cnn_database
    # load_news('/Users/podlipensky/100_days_cnn.csv', db)
    # clean_news(db)
    # remove_rare_words(db)

    # mm, id2word = build_corpora(db)
    mm, id2word = load_corpora()

    # load id->word mapping (the dictionary), one of the results of step 2 above
    # id2word = gensim.corpora.Dictionary.load('data/cnn.dict')
    # load corpus iterator
    # mm = gensim.corpora.MmCorpus('data/corpus.mm')

    lda = gensim.models.ldamodel.LdaModel(corpus=mm, id2word=id2word, num_topics=100, update_every=1, chunksize=1000, passes=10)
    topics = lda.print_topics(50)
    for idx, t in enumerate(topics):
        print idx, t

__main__()