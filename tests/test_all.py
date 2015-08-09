"""Integration tests for the package."""
# pylint: disable=missing-docstring,no-self-use


import yorm
from yorm.converters import Object, String, Integer, Float, Boolean
from yorm.converters import Markdown, Dictionary, List
from yorm.mapper import get_mapper

from . import strip, refresh_file_modification_times


# classes ######################################################################


class EmptyDictionary(Dictionary):

    """Sample dictionary container."""


@yorm.attr(all=Integer)
class IntegerList(List):

    """Sample list container."""


class SampleStandard:

    """Sample class using standard attribute types."""

    def __init__(self):
        # https://docs.python.org/3.4/library/json.html#json.JSONDecoder
        self.object = {}
        self.array = []
        self.string = ""
        self.number_int = 0
        self.number_real = 0.0
        self.true = True
        self.false = False
        self.null = None

    def __repr__(self):
        return "<standard {}>".format(id(self))


@yorm.attr(object=EmptyDictionary, array=IntegerList, string=String)
@yorm.attr(number_int=Integer, number_real=Float)
@yorm.attr(true=Boolean, false=Boolean)
@yorm.sync("path/to/{self.category}/{self.name}.yml")
class SampleStandardDecorated:

    """Sample class using standard attribute types."""

    def __init__(self, name, category='default'):
        self.name = name
        self.category = category
        # https://docs.python.org/3.4/library/json.html#json.JSONDecoder
        self.object = {}
        self.array = []
        self.string = ""
        self.number_int = 0
        self.number_real = 0.0
        self.true = True
        self.false = False
        self.null = None

    def __repr__(self):
        return "<decorated {}>".format(id(self))


@yorm.attr(status=Boolean, label=String)
class StatusDictionary(Dictionary):

    """Sample dictionary container."""


@yorm.attr(all=StatusDictionary)
class StatusDictionaryList(List):

    """Sample list container."""


class Level(String):

    """Sample custom attribute."""

    @classmethod
    def to_data(cls, obj):
        value = cls.to_value(obj)
        count = value.split('.')
        if count == 0:
            return int(value)
        elif count == 1:
            return float(value)
        else:
            return value


@yorm.sync("path/to/directory/{UUID}.yml", attrs={'level': Level})
class SampleCustomDecorated:

    """Sample class using custom attribute types."""

    def __init__(self, name):
        self.name = name
        self.level = '1.0'

    def __repr__(self):
        return "<custom {}>".format(id(self))


@yorm.attr(string=String)
@yorm.sync("sample.yml", auto=False)
class SampleDecoratedAutoOff:

    """Sample class with automatic storage turned off."""

    def __init__(self):
        self.string = ""

    def __repr__(self):
        return "<auto off {}>".format(id(self))


@yorm.sync("sample.yml")
class SampleEmptyDecorated:

    """Sample class using standard attribute types."""

    def __repr__(self):
        return "<empty {}>".format(id(self))


class SampleExtended:

    """Sample class using extended attribute types."""

    def __init__(self):
        self.text = ""

    def __repr__(self):
        return "<extended {}>".format(id(self))


class SampleNested:

    """Sample class using nested attribute types."""

    def __init__(self):
        self.count = 0
        self.results = []

    def __repr__(self):
        return "<nested {}>".format(id(self))

# tests ########################################################################


class TestStandard:  # pylint: disable=no-member

    """Integration tests for standard attribute types."""

    @yorm.attr(status=yorm.converters.Boolean)
    class StatusDictionary(Dictionary):
        pass

    def test_decorator(self, tmpdir):
        """Verify standard attribute types dump/load correctly (decorator)."""
        tmpdir.chdir()
        sample = SampleStandardDecorated('sample')
        assert "path/to/default/sample.yml" == get_mapper(sample).path

        # check defaults
        assert {} == sample.object
        assert [] == sample.array
        assert "" == sample.string
        assert 0 == sample.number_int
        assert 0.0 == sample.number_real
        assert True is sample.true
        assert False is sample.false
        assert None is sample.null

        # change object values
        sample.object = {'key2': 'value'}
        sample.array = [0, 1, 2]
        sample.string = "Hello, world!"
        sample.number_int = 42
        sample.number_real = 4.2
        sample.true = False
        sample.false = True

        # check file values
        assert strip("""
        array:
        - 0
        - 1
        - 2
        'false': true
        number_int: 42
        number_real: 4.2
        object: {}
        string: Hello, world!
        'true': false
        """) == get_mapper(sample).text

        # change file values
        refresh_file_modification_times()
        get_mapper(sample).text = strip("""
        array: [4, 5, 6]
        'false': null
        number_int: 42
        number_real: '4.2'
        object: {'status': false}
        string: "abc"
        'true': null
        """)

        # check object values
        assert {'status': False} == sample.object
        assert [4, 5, 6] == sample.array
        assert "abc" == sample.string
        assert 42 == sample.number_int
        assert 4.2 == sample.number_real
        assert False is sample.true
        assert False is sample.false

    def test_function(self, tmpdir):
        """Verify standard attribute types dump/load correctly (function)."""
        tmpdir.chdir()
        _sample = SampleStandard()
        attrs = {'object': self.StatusDictionary,
                 'array': IntegerList,
                 'string': String,
                 'number_int': Integer,
                 'number_real': Float,
                 'true': Boolean,
                 'false': Boolean}
        sample = yorm.sync(_sample, "path/to/directory/sample.yml", attrs)
        assert "path/to/directory/sample.yml" == get_mapper(sample).path

        # check defaults
        assert {'status': False} == sample.object
        assert [] == sample.array
        assert "" == sample.string
        assert 0 == sample.number_int
        assert 0.0 == sample.number_real
        assert True is sample.true
        assert False is sample.false
        assert None is sample.null

        # change object values
        sample.object = {'key': 'value'}
        sample.array = [1, 2, 3]
        sample.string = "Hello, world!"
        sample.number_int = 42
        sample.number_real = 4.2
        sample.true = None
        sample.false = 1

        # check file values
        assert strip("""
        array:
        - 1
        - 2
        - 3
        'false': true
        number_int: 42
        number_real: 4.2
        object:
          status: false
        string: Hello, world!
        'true': false
        """) == get_mapper(sample).text

    def test_auto_off(self, tmpdir):
        """Verify file updates are disabled with auto off."""
        tmpdir.chdir()
        sample = SampleDecoratedAutoOff()

        # ensure the file does not exist
        assert False is get_mapper(sample).exists
        assert "" == get_mapper(sample).text

        # store value
        sample.string = "hello"

        # ensure the file still does not exist
        assert False is get_mapper(sample).exists
        assert "" == get_mapper(sample).text

        # enable auto and store value
        get_mapper(sample).auto = True
        sample.string = "world"

        # check for changed file values
        assert strip("""
        string: world
        """) == get_mapper(sample).text


class TestContainers:  # pylint: disable=no-member

    """Integration tests for attribute containers."""

    def test_nesting(self, tmpdir):
        """Verify standard attribute types can be nested."""
        tmpdir.chdir()
        _sample = SampleNested()
        attrs = {'count': Integer,
                 'results': StatusDictionaryList}
        sample = yorm.sync(_sample, "sample.yml", attrs)

        # check defaults
        assert 0 == sample.count
        assert [] == sample.results

        # change object values
        sample.count = 5
        sample.results = [{'status': False, 'label': "abc"},
                          {'status': None, 'label': None},
                          {'label': "def"},
                          {'status': True},
                          {}]

        # check file values
        assert strip("""
        count: 5
        results:
        - label: abc
          status: false
        - label: ''
          status: false
        - label: def
          status: false
        - label: ''
          status: true
        - label: ''
          status: false
        """) == get_mapper(sample).text

        # change file values
        refresh_file_modification_times()
        get_mapper(sample).text = strip("""
        count: 3
        other: 4.2
        results:
        - label: abc
        - label: null
          status: false
        - status: true
        """)

        # check object values
        assert 3 == sample.count
        assert 4.2 == sample.other
        assert [{'label': 'abc', 'status': False},
                {'label': '', 'status': False},
                {'label': '', 'status': True}] == sample.results

    def test_objects(self, tmpdir):
        """Verify containers are treated as objects when added."""
        tmpdir.chdir()
        sample = SampleEmptyDecorated()

        # change file values
        refresh_file_modification_times()
        get_mapper(sample).text = strip("""
        object: {'key': 'value'}
        array: [1, '2', '3.0']
        """)

        # (a mapped attribute must be read first to trigger retrieving)
        get_mapper(sample).fetch()

        # check object values
        assert {'key': 'value'} == sample.object
        assert [1, '2', '3.0'] == sample.array

        # check object types
        assert Object == get_mapper(sample).attrs['object']
        assert Object == get_mapper(sample).attrs['array']

        # change object values
        sample.object = None  # pylint: disable=W0201
        sample.array = "abc"  # pylint: disable=W0201

        # check file values
        assert strip("""
        array: abc
        object: null
        """) == get_mapper(sample).text


class TestExtended:

    """Integration tests for extended attribute types."""

    def test_function(self, tmpdir):
        """Verify extended attribute types dump/load correctly."""
        tmpdir.chdir()
        _sample = SampleExtended()
        attrs = {'text': Markdown}
        sample = yorm.sync(_sample, "path/to/directory/sample.yml", attrs)

        # check defaults
        assert "" == sample.text

        # change object values
        refresh_file_modification_times()
        sample.text = strip("""
        This is the first sentence. This is the second sentence.
        This is the third sentence.
        """)

        # check file values
        assert strip("""
        text: |
          This is the first sentence.
          This is the second sentence.
          This is the third sentence.
        """) == get_mapper(sample).text

        # change file values
        refresh_file_modification_times()
        get_mapper(sample).text = strip("""
        text: |
          This is a
          sentence.
        """)

        # check object values
        assert "This is a sentence." == sample.text


class TestCustom:

    """Integration tests for custom attribute types."""

    def test_decorator(self, tmpdir):
        """Verify custom attribute types dump/load correctly."""
        tmpdir.chdir()
        sample = SampleCustomDecorated('sample')

        # check defaults
        assert '1.0' == sample.level

        # change values
        sample.level = '1.2.3'

        # check file values
        assert strip("""
        level: 1.2.3
        """) == get_mapper(sample).text

        # change file values
        refresh_file_modification_times()
        get_mapper(sample).text = strip("""
        level: 1
        """)

        # check object values
        assert '1' == sample.level
