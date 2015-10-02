# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

from collections import MutableMapping, Mapping
from copy import deepcopy

from pyLibrary.dot import split_field, _getdefault, hash_value, literal_field, coalesce, listwrap


_get = object.__getattribute__
_set = object.__setattr__

DEBUG = False


class Dict(MutableMapping):
    """
    Please see README.md
    """

    __slots__ = ["_dict"]

    def __init__(self, *args, **kwargs):
        """
        CALLING Dict(**something) WILL RESULT IN A COPY OF something, WHICH
        IS UNLIKELY TO BE USEFUL. USE wrap() INSTEAD
        """
        if DEBUG:
            d = _get(self, "_dict")
            for k, v in kwargs.items():
                d[literal_field(k)] = unwrap(v)
        else:
            if args:
                args0=args[0]
                if isinstance(args0, Mapping):
                    _set(self, "_dict", args0)
                else:
                    _set(self, "_dict", _get(args[0], "__dict__"))
            elif kwargs:
                _set(self, "_dict", unwrap(kwargs))
            else:
                _set(self, "_dict", {})

    def __bool__(self):
        return True

    def __nonzero__(self):
        d = _get(self, "_dict")
        return True if d else False

    def __contains__(self, item):
        if Dict.__getitem__(self, item):
            return True
        return False

    def __iter__(self):
        d = _get(self, "_dict")
        return d.__iter__()

    def __getitem__(self, key):
        if key == None:
            return Null
        if key == ".":
            output = _get(self, "_dict")
            if isinstance(output, Mapping):
                return self
            else:
                return output

        if isinstance(key, str):
            key = key.decode("utf8")
        elif not isinstance(key, unicode):
            from pyLibrary.debugs.logs import Log
            Log.error("only string keys are supported")

        d = _get(self, "_dict")

        if key.find(".") >= 0:
            seq = split_field(key)
            for n in seq:
                d = _getdefault(d, n)
            return wrap(d)
        else:
            o = d.get(key)

        if o == None:
            return NullType(d, key)
        return wrap(o)

    def __setitem__(self, key, value):
        if key == "":
            from pyLibrary.debugs.logs import Log

            Log.error("key is empty string.  Probably a bad idea")
        if key == ".":
            # SOMETHING TERRIBLE HAPPENS WHEN value IS NOT A Mapping;
            # HOPEFULLY THE ONLY OTHER METHOD RUN ON self IS unwrap()
            v = unwrap(value)
            _set(self, "_dict", v)
            return v
        if isinstance(key, str):
            key = key.decode("utf8")

        try:
            d = _get(self, "_dict")
            value = unwrap(value)
            if key.find(".") == -1:
                if value is None:
                    d.pop(key, None)
                else:
                    d[key] = value
                return self

            seq = split_field(key)
            for k in seq[:-1]:
                d = _getdefault(d, k)
            if value == None:
                d.pop(seq[-1], None)
            else:
                d[seq[-1]] = value
            return self
        except Exception, e:
            raise e

    def __getattr__(self, key):
        if isinstance(key, str):
            ukey = key.decode("utf8")
        else:
            ukey = key

        d = _get(self, "_dict")
        o = d.get(ukey)
        if o == None:
            return NullType(d, ukey)
        return wrap(o)

    def __setattr__(self, key, value):
        if isinstance(key, str):
            ukey = key.decode("utf8")
        else:
            ukey = key

        d = _get(self, "_dict")
        value = unwrap(value)
        if value is None:
            d = _get(self, "_dict")
            d.pop(key, None)
        else:
            d[ukey] = value
        return self

    def __hash__(self):
        d = _get(self, "_dict")
        return hash_value(d)

    def __eq__(self, other):
        if self is other:
            return True

        d = _get(self, "_dict")
        if not d and other == None:
            return True

        if not isinstance(other, Mapping):
            return False
        e = unwrap(other)
        d = _get(self, "_dict")
        for k, v in d.items():
            if e.get(k) != v:
                return False
        for k, v in e.items():
            if d.get(k) != v:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def get(self, key, default=None):
        d = _get(self, "_dict")
        return d.get(key, default)

    def items(self):
        d = _get(self, "_dict")
        return [(k, wrap(v)) for k, v in d.items() if v != None or isinstance(v, Mapping)]

    def leaves(self, prefix=None):
        """
        LIKE items() BUT RECURSIVE, AND ONLY FOR THE LEAVES (non dict) VALUES
        """
        prefix = coalesce(prefix, "")
        output = []
        for k, v in self.items():
            if isinstance(v, Mapping):
                output.extend(wrap(v).leaves(prefix=prefix + literal_field(k) + "."))
            else:
                output.append((prefix + literal_field(k), v))
        return output

    def iteritems(self):
        # LOW LEVEL ITERATION, NO WRAPPING
        d = _get(self, "_dict")
        return ((k, wrap(v)) for k, v in d.iteritems())

    def keys(self):
        d = _get(self, "_dict")
        return set(d.keys())

    def values(self):
        d = _get(self, "_dict")
        return listwrap(d.values())

    def clear(self):
        from pyLibrary.debugs.logs import Log
        Log.error("clear() not supported")

    def __len__(self):
        d = _get(self, "_dict")
        return dict.__len__(d)

    def copy(self):
        return Dict(**self)

    def __copy__(self):
        d = _get(self, "_dict")
        return Dict(**d)

    def __deepcopy__(self, memo):
        d = _get(self, "_dict")
        return wrap(deepcopy(d, memo))

    def __delitem__(self, key):
        if isinstance(key, str):
            key = key.decode("utf8")

        if key.find(".") == -1:
            d = _get(self, "_dict")
            d.pop(key, None)
            return

        d = _get(self, "_dict")
        seq = split_field(key)
        for k in seq[:-1]:
            d = d[k]
        d.pop(seq[-1], None)

    def __delattr__(self, key):
        if isinstance(key, str):
            key = key.decode("utf8")

        d = _get(self, "_dict")
        d.pop(key, None)

    def setdefault(self, k, d=None):
        if self[k] == None:
            self[k] = d
        return self

    def __str__(self):
        try:
            return "Dict("+dict.__str__(_get(self, "_dict"))+")"
        except Exception, e:
            return "Dict{}"

    def __repr__(self):
        try:
            return "Dict("+dict.__repr__(_get(self, "_dict"))+")"
        except Exception, e:
            return "Dict()"


class _DictUsingSelf(dict):

    def __init__(self, **kwargs):
        """
        CALLING Dict(**something) WILL RESULT IN A COPY OF something, WHICH
        IS UNLIKELY TO BE USEFUL. USE wrap() INSTEAD
        """
        dict.__init__(self)

    def __bool__(self):
        return True

    def __getitem__(self, key):
        if key == None:
            return Null
        if isinstance(key, str):
            key = key.decode("utf8")

        d=self
        if key.find(".") >= 0:
            seq = split_field(key)
            for n in seq:
                d = _getdefault(self, n)
            return wrap(d)
        else:
            o = dict.get(d, None)

        if o == None:
            return NullType(d, key)
        return wrap(o)

    def __setitem__(self, key, value):
        if key == "":
            from pyLibrary.debugs.logs import Log

            Log.error("key is empty string.  Probably a bad idea")
        if isinstance(key, str):
            key = key.decode("utf8")
        d=self
        try:
            value = unwrap(value)
            if key.find(".") == -1:
                if value is None:
                    dict.pop(d, key, None)
                else:
                    dict.__setitem__(d, key, value)
                return self

            seq = split_field(key)
            for k in seq[:-1]:
                d = _getdefault(d, k)
            if value == None:
                dict.pop(d, seq[-1], None)
            else:
                dict.__setitem__(d, seq[-1], value)
            return self
        except Exception, e:
            raise e

    def __getattr__(self, key):
        if isinstance(key, str):
            ukey = key.decode("utf8")
        else:
            ukey = key

        d = self
        o = dict.get(d, ukey, None)
        if o == None:
            return NullType(d, ukey)
        return wrap(o)

    def __setattr__(self, key, value):
        if isinstance(key, str):
            ukey = key.decode("utf8")
        else:
            ukey = key

        d = self
        value = unwrap(value)
        if value is None:
            dict.pop(d, key, None)
        else:
            dict.__setitem__(d, ukey, value)
        return self

    def __hash__(self):
        return hash_value(self)

    def __eq__(self, other):
        if self is other:
            return True

        d = self
        if not d and other == None:
            return True

        if not isinstance(other, Mapping):
            return False
        e = unwrap(other)
        for k, v in dict.items(d):
            if e.get(k) != v:
                return False
        for k, v in e.items():
            if dict.get(d, k, None) != v:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def get(self, key, default=None):
        return wrap(dict.get(self, key, default))

    def items(self):
        return [(k, wrap(v)) for k, v in dict.items(self) if v != None or isinstance(v, Mapping)]

    def leaves(self, prefix=None):
        """
        LIKE items() BUT RECURSIVE, AND ONLY FOR THE LEAVES (non dict) VALUES
        """
        prefix = coalesce(prefix, "")
        output = []
        for k, v in self.items():
            if isinstance(v, Mapping):
                output.extend(wrap(v).leaves(prefix=prefix + literal_field(k) + "."))
            else:
                output.append((prefix + literal_field(k), v))
        return output

    def iteritems(self):
        for k, v in dict.iteritems(self):
            yield k, wrap(v)

    def keys(self):
        return set(dict.keys(self))

    def values(self):
        return listwrap(dict.values(self))

    def clear(self):
        from pyLibrary.debugs.logs import Log
        Log.error("clear() not supported")

    def __len__(self):
        d = _get(self, "_dict")
        return d.__len__()

    def copy(self):
        return Dict(**self)

    def __copy__(self):
        return Dict(**self)

    def __deepcopy__(self, memo):
        return wrap(dict.__deepcopy__(self, memo))

    def __delitem__(self, key):
        if isinstance(key, str):
            key = key.decode("utf8")

        if key.find(".") == -1:
            dict.pop(self, key, None)
            return

        d = self
        seq = split_field(key)
        for k in seq[:-1]:
            d = d[k]
        d.pop(seq[-1], None)

    def __delattr__(self, key):
        if isinstance(key, str):
            key = key.decode("utf8")

        dict.pop(self, key, None)

    def setdefault(self, k, d=None):
        if self[k] == None:
            self[k] = d
        return self

    def __str__(self):
        try:
            return dict.__str__(self)
        except Exception, e:
            return "{}"

    def __repr__(self):
        try:
            return "Dict("+dict.__repr__(self)+")"
        except Exception, e:
            return "Dict()"



# KEEP TRACK OF WHAT ATTRIBUTES ARE REQUESTED, MAYBE SOME (BUILTIN) ARE STILL USEFUL
requested = set()


def _str(value, depth):
    """
    FOR DEBUGGING POSSIBLY RECURSIVE STRUCTURES
    """
    output = []
    if depth >0 and isinstance(value, Mapping):
        for k, v in value.items():
            output.append(str(k) + "=" + _str(v, depth - 1))
        return "{" + ",\n".join(output) + "}"
    elif depth >0 and isinstance(value, list):
        for v in value:
            output.append(_str(v, depth-1))
        return "[" + ",\n".join(output) + "]"
    else:
        return str(type(value))


from pyLibrary.dot.nones import Null, NullType
from pyLibrary.dot import unwrap, wrap
