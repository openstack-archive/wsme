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


class BookNotFound(Exception):
    message = "Book with ID={id} Not Found"
    code = 404

    def __init__(self, id):
        message = self.message.format(id=id)
        super(BookNotFound, self).__init__(message)


class BooksController(RestController):

    @wsmeext.pecan.wsexpose(Book, int, int)
    def get(self, author_id, id):
        print repr(author_id), repr(id)
        book = Book(
            name=u"Les Confessions d’un révolutionnaire pour servir à "
                 u"l’histoire de la révolution de février",
            author=Author(lastname=u"Proudhon")
        )
        return book

    @wsmeext.pecan.wsexpose(Book, int, int, body=Book)
    def put(self, author_id, id, book=None):
        print author_id, id
        print book
        book.id = id
        book.author = Author(id=author_id)
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

        if id == 998:
            raise BookNotFound(998)

        if id == 911:
            return wsme.api.Response(Author(),
                                     status_code=401)
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

    @wsmeext.pecan.wsexpose(Author, body=Author, status_code=201)
    def post(self, author):
        author.id = 10
        return author

    @wsmeext.pecan.wsexpose(None, int)
    def delete(self, author_id):
        print "Deleting", author_id
