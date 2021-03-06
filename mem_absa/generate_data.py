


import tensorflow as tf

import pickle
import numpy as np
import re
from mem_absa.load_data import init_word_embeddings
from mem_absa.load_data import read_sample, read_vocabulary
from mem_absa.mapping import mapping_sentiments
from mem_absa.model import MemN2N
from mem_absa.config_mem import Configure

import spacy
fr_nlp=spacy.load("fr")
path=".."
configure=Configure()
FLAGS=configure.get_flags(path)

from pyfasttext import FastText
wiki_model=FastText()
wiki_model.load_model(FLAGS.pathFasttext)

def main(_):
    configure.pp.pprint(FLAGS.__flags)
    source_count=[]
    source_word2idx={}

    read_vocabulary(fr_nlp,FLAGS.train_data, source_count, source_word2idx)

    print('loading pre-trained word vectors...')
    FLAGS.pre_trained_context_wt=init_word_embeddings(wiki_model,source_word2idx, FLAGS.nbwords)
    FLAGS.pre_trained_context_wt[FLAGS.pad_idx, :]=0


    model=MemN2N(FLAGS)
    model.build_model()
    saver=tf.train.Saver(tf.trainable_variables())


    print('Loading Model...')
    ckpt=tf.train.get_checkpoint_state(FLAGS.pathModel)
    saver.restore(model.sess, ckpt.model_checkpoint_path)
    print("Model loaded")


    with open(FLAGS.test_samples, "r") as f:
        reviews=[]
        for line in f:
            reviews.append(line)

    with open(FLAGS.test_aspects, 'rb') as fp:
        aspects=pickle.load(fp)

    for review, aspects_ in zip(reviews, aspects):
        print("\n", review, end='')
        if len(aspects_) > 0:
            aspect_words=np.array(aspects_)[:, 0]
            aspect_categories=np.array(aspects_)[:, 1]
            aspect_idx=np.array(aspects_)[:, 2]
            print(aspect_words,aspect_categories,aspect_idx)
            test_data=read_sample(fr_nlp,review, aspect_words,aspect_idx, source_count, source_word2idx)
            FLAGS.pre_trained_context_wt=init_word_embeddings(wiki_model,source_word2idx, FLAGS.nbwords)
            FLAGS.pre_trained_context_wt[FLAGS.pad_idx, :]=0

            predictions=model.predict(test_data, source_word2idx)
            samples={}
            for asp, cat, idx, pred in zip(aspect_words, aspect_categories, aspect_idx, predictions):
                print(asp, " : ", str(cat), " =>", mapping_sentiments(pred),end=" ; ")
                sample=[s.strip() for s in re.split('[\.\?!,;:]', review) if
                        re.sub(' ', '', asp.lower()) in re.sub(' ', '', s.lower())][0]

                print(sample)
                samples[str(cat)+'_'+str(pred)]=sample

            #summary review
            print("\n------SUMMARY REVIEW-------")
            categories=['SERVICE','AMBIANCE','QUALITE','PRIX','GENERAL','LOCALISATION']
            for categ in categories:
                exists=False
                total=0
                val=0
                for asp, cat, pred in zip(aspect_words, aspect_categories, predictions):
                    #print(mapping(str(cat)),categ)
                    if str(cat)==categ:
                        exists=True
                        total+=1
                        val+=pred
                if exists:
                    #print(categ, " ", mapping_sentiments(round(val / total)))
                    #print(samples)
                    #print(categ+'_'+str(int(round(val/total))))
                    print(categ," ",mapping_sentiments(round(val/total)),"exemple : ",samples[categ+'_'+str(int(round(val/total)))])
        else:
            print("PAS D'ASPECTS !")


if __name__ == '__main__':
    tf.app.run()
