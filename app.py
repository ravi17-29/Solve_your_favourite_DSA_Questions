from flask import Flask, jsonify
import math
import re

from flask import Flask, render_template, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

app = Flask(__name__)
# , static_url_path='/static', static_folder='/static'
def load_vocab():
    vocab = {}
    with open('tf-idf/vocab.txt', "r") as f:
        vocab_terms = f.readlines()
    with open('tf-idf/idf-values.txt', 'r') as f:
        idf_values = f.readlines()

    for (term, idf_value) in zip(vocab_terms, idf_values):
        vocab[term.strip()] = int(idf_value.strip())

    return vocab


def load_documents():
    # documents = []
    with open("tf-idf/documents.txt", "r") as f:
        documents = f.readlines()
    # documents = [document.strip().split() for document in documents]

    # print('Number of documents: ', len(documents))
    # print('Sample document: ', documents[0])
    return documents


def load_inverted_index():
    inverted_index = {}
    with open('tf-idf/inverted-index.txt', 'r') as f:
        inverted_index_terms = f.readlines()

    for row_num in range(0, len(inverted_index_terms), 2):
        term = inverted_index_terms[row_num].strip()
        documents = inverted_index_terms[row_num + 1].strip().split()
        inverted_index[term] = documents

    # print('Size of inverted index: ', len(inverted_index))
    return inverted_index


def load_link_of_qs():
    with open("Qdata/Qindex.txt", "r") as f:
        links = f.readlines()

    return links


def load_name_of_qs():
    with open("Qdata/index.txt", "r") as f:
        name = f.readlines()

    return name


vocab_idf_values = load_vocab()
documents = load_documents()
inverted_index = load_inverted_index()
Qlink = load_link_of_qs()
Qname = load_name_of_qs()


# print(Qname)
# print(Qlink)

def get_tf_dictionary(term):
    tf_values = {}
    if term in inverted_index:
        for document in inverted_index[term]:
            if document not in tf_values:
                tf_values[document] = 1
            else:
                tf_values[document] += 1

    for document in tf_values:

        try:
            tf_values[document] /= len(documents[int(document)])
        except (ZeroDivisionError, ValueError, IndexError) as e:
            print(e)
            print(document)
    return tf_values


def get_idf_value(term):
    return math.log((1 + len(documents) / (1+vocab_idf_values[term])))


def calculate_sorted_order_of_documents(query_terms):
    potential_documents = {}
    ans = []
    for term in query_terms:
        if term not in vocab_idf_values:
            continue
        tf_values_by_document = get_tf_dictionary(term)
        idf_value = get_idf_value(term)
        # print(term, tf_values_by_document, idf_value)
        for document in tf_values_by_document:
            if document not in potential_documents:
                potential_documents[document] = tf_values_by_document[document] * idf_value
            else:
                potential_documents[document] += tf_values_by_document[document] * idf_value

    # print(potential_documents)
    # divide by the length of the query terms
    for document in potential_documents:
        potential_documents[document] /= len(query_terms)

    potential_documents = dict(sorted(potential_documents.items(), key=lambda item: item[1], reverse=True))

    if len(potential_documents) == 0:
        print("No matching question found. Please search with more relevant terms.")
        # message = "No matching question found. Please search with more relevant terms."



    for document_index in potential_documents:
        # print('Document: ', documents[int(document_index)], ' Score: ', potential_documents[document_index])
        ans.append(
            {"Question Link": Qlink[int(document_index) - 1][:-2],
             "names":re.sub(r'[^a-zA-Z\s]', '', Qname[int(document_index) - 1]),
             ' Score': potential_documents[document_index]}
        )
    return ans

app.config['SECRET_KEY'] = 'your-secret-key'


# class SearchForm(FlaskForm):
#     search = StringField(' ', render_kw={'class': 'search-field'}, description='Search here...')
#     submit = SubmitField('search ', render_kw={'class': 'submit-button'})


class NavbarSearchForm(FlaskForm):
    search = StringField('',render_kw={'class': 'form-control me-2', 'placeholder': 'Enter your favourite Question'})
    submit = SubmitField('search', render_kw={'class': 'btn btn-outline-success'})

    def move_search_button(self):
        self.submit.render_kw['class'] += ' moved'

@app.route("/<query>")
def return_links(query):
    q_terms = [term.lower() for term in query.strip().split()]
    return jsonify(calculate_sorted_order_of_documents(q_terms)[:3000:])


@app.route("/", methods=['GET', 'POST'])
def home():
    form = NavbarSearchForm()
    results = []
    if form.validate_on_submit():
        query = form.search.data
        q_terms = [term.lower() for term in query.strip().split()]
        results = calculate_sorted_order_of_documents(q_terms)[:3000:]
    return render_template('index.html', form=form, results=results)