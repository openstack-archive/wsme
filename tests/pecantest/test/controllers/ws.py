# encoding=utf8
from pecan.rest import RestController

from wsme.types import Base, text, wsattr

import wsme
import wsmeext.pecan


class Author(Base):
    id = int
    firstname = text
    books = wsattr(['Book'])


class Book(Base):
    id = int
    name = text
    author = wsattr('Author')


class BooksController(RestController):

    @wsmeext.pecan.wsexpose(Book, int, int)
    def get(self, author_id, id):
        print repr(author_id), repr(id)
        book = Book(
            name=u"Les Confessions d’un révolutionnaire pour servir à "
                 u"l’histoire de la révolution de février",
            author=Author(lastname=u"Proudhon"))
        return book

    @wsmeext.pecan.wsexpose(Book, int, int, body=Book)
    def put(self, author_id, id, book=None):
        print author_id, id
        print book
        return book


class Criterion(Base):
    op = text
    attrname = text
    value = text


class AuthorsController(RestController):

    books = BooksController()

    @wsmeext.pecan.wsexpose([Author], [unicode], [Criterion])
    def get_all(self, q=None, r=None):
        if q:
            return [
                Author(id=i, firstname=value)
                for i, value in enumerate(q)
            ]
        if r:
            return [
                Author(id=i, firstname=c.value)
                for i, c in enumerate(r)
            ]
        return [
            Author(id=1, firstname=u'FirstName')
        ]

    @wsmeext.pecan.wsexpose(Author, int)
    def get(self, id):
        if id == 999:
            raise wsme.exc.ClientSideError('Wrong ID')
        author = Author()
        author.id = id
        author.firstname = u"aname"
        author.books = [
            Book(
                name=u"Les Confessions d’un révolutionnaire pour servir à "
                    u"l’histoire de la révolution de février",
            )
        ]
        return author
