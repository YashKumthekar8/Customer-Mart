from django.test import TestCase

from typing import Dict, Text
import numpy as np
import pandas as pd
import tensorflow as tf
import tensorflow_datasets as tfds
import tensorflow_recommenders as tfrs
from .models import *
from sklearn.decomposition import TruncatedSVD


class ProductRatingModel(tfrs.models.Model):
    def _init_(self, rating_weight: float, retrieval_weight: float,unique_product_titles,unique_user_ids_ratings,products) -> None:
        super()._init_()
        embedding_dimension = 32
        self.product_model: tf.keras.layers.Layer = tf.keras.Sequential([
            tf.keras.layers.Stringlookup(vocabulary=unique_product_titles, mask_token=None),
            tf.keras.layers.Embedding(len(unique_product_titles) + 1, embedding_dimension),
        ])

        self.user_model: tf.keras.layers.Layer = tf.keras.Sequential([
            tf.keras.layers.Stringlookup(vocabulary=unique_user_ids_ratings, mask_token=None),
            tf.keras.layers.Embedding(len(unique_user_ids_ratings) + 1, embedding_dimension),
        ])

        self.rating_model = tf.keras.Sequential([
            tf.keras.layers.Dense(256, activaion='relu'),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(1),
        ])

        self.rating_task: tf.keras.layers.Layer = tfrs.tasks.Ranking(loss=tf.keras.losses.MeanSquaredError(), metrics=[tf.keras.metrics.RootMeanSquaredError()],)

        self.retrieval_task: tf.keras.layers.Layer = tfrs.tasks.Retrieval(metrics=tfrs.metrics.FactorizedTopK(candidates=products.map(self.product_model)))

        self.rating_weight = rating_weight
        self.retrieval_weight = retrieval_weight

    def _call_(self, features: Dict[Text, tf.Tensor]) -> tf.Tensor:
        user_embeddings = self.user_model(features['user_id'])
        product_embeddings = self.product_model(features['product_title'])
        return (user_embeddings, product_embeddings, self.rating_model(tf.concat([user_embeddings, product_embeddings], axis=1)))

    def compute_loss(self, features: Dict[Text, tf.Tensor], training: bool = False) -> tf.Tensor:
        ratings = features.pop('user_rating')
        user_embeddings, product_embeddings, rating_predictions = self(features)
        rating_loss = self.rating_task(labels=ratings, predictions=rating_predictions)
        retrieval_loss = self.retrieval_task(user_embeddings, product_embeddings)
        return self.rating_weight * rating_loss + self.retrieval_weight * retrieval_loss



def fetch_data(userid):
    products = pd.DataFrame(list(Product.objects.all().values()))
    carts = pd.DataFrame(list(CartCount.objects.all().values()))
    views = pd.DataFrame(list(ViewCount.objects.all().values()))
    ratings = pd.DataFrame(list(Rating.objects.all().values()))
    ratings['userid'] = ratings['userid'].apply(str)
    ratings['rating'] = ratings['rating'].astype(float)
    data = preprocess(ratings,products,userid)
    popular_cart_products, popular_view_products = cart_view_prediction(carts, views)
    recommended_products_ratings = []
    for i in range(0, data.shape[0]):
        recommended_products_ratings.append(data[i].numpy().decode())

    recommended_products_util = common_recommended_products(recommended_products_ratings, popular_cart_products)
    recommended_products = common_recommended_products(recommended_products_util, popular_view_products)

    recommended_products = recommended_products + recommended_products_util
    recommended_products = recommended_products + recommended_products_ratings

    if len(recommended_products) > 5:
        extra_elements = len(recommended_products) - 5
        del recommended_products[-extra_elements]
    
    return recommended_products

def common_recommended_products(list1, list2):
    return list(set(list1) & set(list2))



def preprocess(ratings, products,userid):
    ratings = ratings[['pname', 'userid', 'rating']]
    ratings = tf.data.Dataset.from_tensor_slices(ratings.to_dict(orient='list'))
    products = tf.data.Dataset.from_tensor_slices(products.to_dict(orient='list'))
    ratings = ratings.map(lambda x: {
    'product_title': x['pname'],
    'user_id': x['userid'],
    'user_rating': x['rating'],
    })
    products = products.map(lambda x: x['pname'])
    rating_shape = len(ratings)
    return make_train_test(ratings, products,rating_shape,userid)


def make_train_test(ratings, products, ratings_shape,userid):
    tf.random.set_seed(42)
    ratings_shuffled = ratings.shuffle(ratings_shape, seed=42, reshuffle_each_iteration=False)
    ratings_train = ratings_shuffled.take(round(0.8 * ratings_shape))
    length = round(0.8 * ratings_shape)
    ratings_test = ratings_shuffled.skip(round(0.8 * ratings_shape)).take(ratings_shape - length)
    product_titles = products.batch(ratings_shape)
    unique_product_titles = np.unique(np.concatenate(list(product_titles)))
    user_ids_ratings = ratings.batch(10 * ratings_shape).map(lambda x: x['user_id'])
    unique_user_ids_ratings = np.unique(np.concatenate(list(user_ids_ratings)))
    return train_model(ratings_shape,ratings_train,ratings_test,products,unique_product_titles,unique_user_ids_ratings,userid) 

def train_model(ratings_shape, ratings_train, ratings_test,products,unique_product_titles,unique_user_ids_ratings,userid):
    ratings_model = ProductRatingModel(rating_weight=1.0, retrieval_weight=1.0,unique_product_titles=unique_product_titles,unique_user_ids_ratings=unique_user_ids_ratings,products=products)
    ratings_model.load_weights('./checkpoints/my_checkpoint')
    try:
        ratings_model.compile(optimizer=tf.keras.optimizers.Adagrad(0.1))
        cached_train = ratings_train.shuffle(ratings_shape).batch(4).cache()
        cached_test = ratings_test.batch(2).cache()
        ratings_model.fit(cached_train, epochs=10)
        metrics = ratings_model.evaluate(cached_test, return_dict=True)
        brute_force = tfrs.layers.factorized_top_k.BruteForce(ratings_model.user_model)
        brute_force.index_from_dataset(products.batch(128).map(lambda title: (title, ratings_model.product_model(title))))
        _, titles_based_on_ratings = brute_force(np.array([str(userid)]), k = 5)
        return titles_based_on_ratings[0]
    except:    
        print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    finally:    
        brute_force = tfrs.layers.factorized_top_k.BruteForce(ratings_model.user_model)
        brute_force.index_from_dataset(products.batch(128).map(lambda title: (title, ratings_model.product_model(title))))
        _, titles_based_on_ratings = brute_force(np.array([str(userid)]), k = 5)
        return titles_based_on_ratings[0]

def cart_view_prediction(carts, views):
    popular_cart_products = carts.sort_values(by=['count'], ascending=False)
    popular_view_products = views.sort_values(by=['count'], ascending=False)
    return popular_cart_products, popular_view_products



# For new users
def collaborativeFiltering():
    ratings = pd.DataFrame(Rating.objects.all())
    ratings_with_id = ratings[['pname', 'userid', 'rating']]
    # Need to find product_id using pname
    popular_products = pd.DataFrame(ratings_with_id.groupby('product_id')['rating'].count())
    most_popular = popular_products.sort_values('rating', ascending=False)
    ratings_utility_matrix = ratings_with_id.pivot_table(values='rating', index='userid', columns='product_id', fill_Value=0)
    X = ratings_utility_matrix.T
    X1 = X
    svd = TruncatedSVD(n_components=10)
    decomposed_matrix = svd.fit_transform(X)
    correlation_matrix = np.corrcoef(decomposed_matrix)
    product_ = 1
    product_titles = list(X.index)
    product_id = product_titles.index(product_)
    correlation_product_id = correlation_matrix[product_id]
    recommend = list(X.index[correlation_product_id > 0.90])
    recommend.remove(product_)
    return recommend[0: 9]