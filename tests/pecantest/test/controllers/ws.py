# encoding=utf8
from pecan.rest import RestController

from wsme.types import Base, text, wsattr

import wsme
import wsme.pecan


class Author(Base):
    id = int
    firstname = text
    books = wsattr(['Book'])


class Book(Base):
    id = int
    name = text
    author = wsattr('Author')


class BooksController(RestController):

    @wsme.pecan.wsexpose(Book, int, int)
    def get(self, author_id, id):
        print repr(author_id), repr(id)
        book = Book(
            name=u"Les Confessions d’un révolutionnaire pour servir à "
                 u"l’histoire de la révolution de février",
            author=Author(lastname=u"Proudhon"))
        return book

    @wsme.pecan.wsexpose(Book, int, int, body=Book)
    def put(self, author_id, id, book=None):
        print author_id, id
        print book
        return book


class AuthorsController(RestController):

    books = BooksController()

    @wsme.pecan.wsexpose(Author, int)
    def get(self, id):
        author = Author()
        author.id = id
        author.name = u"aname"
        return author
