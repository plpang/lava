# Copyright (C) 2021 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause
# See: https://spdx.org/licenses/
import typing as ty

from lava.magma.core.model.model import AbstractProcessModel
from lava.magma.core.process.process import AbstractProcess
from lava.magma.core.resources import AbstractResource
from lava.magma.core.sync.protocol import AbstractSyncProtocol


def implements(proc: ty.Optional[ty.Type[AbstractProcess]] = None,
               protocol: ty.Optional[ty.Type[AbstractSyncProtocol]] = None):
    """Decorates ProcessModel class by adding the class of the Process and
    SyncProtocol that this ProcessModel implements as a class variable.

    'implements' will fail if an attempt is made to overwrite an already set
    Process or SyncProtocol class of a parent class.

    Parameters
    ----------
    proc: The Process class that the ProcessModel implements.
    protocol: The SyncProtocol tht the ProcessModel implements.
    """

    if proc:
        if not issubclass(proc, AbstractProcess):
            raise AssertionError
    if protocol:
        if not issubclass(protocol, AbstractSyncProtocol):
            raise AssertionError

    def decorate_process_model(cls: type):
        if not issubclass(cls, AbstractProcessModel):
            raise AssertionError("Decorated class must be a \
            subclass of 'AbstractProcessModel'.")

        # Check existing 'implements_process' does not get overwritten by a
        # different process
        if cls.implements_process and proc and cls.implements_process != proc:
            raise AssertionError(
                f"ProcessModel '{cls.__name__}' already implements a "
                f"Process (perhaps due to sub classing).")

        # Only set which Process the ProcessModel implements if not 'None'
        if proc:
            # Reset attribute on this class to not overwrite parent class
            setattr(cls, 'implements_process', proc)

        # Check existing 'implements_protocol' does not get overwritten by a
        # different protocol
        if cls.implements_protocol and protocol and \
                cls.implements_protocol != protocol:
            raise AssertionError(
                f"ProcessModel '{cls.__name__}' already implements a "
                f"SyncProtocol (perhaps due to sub classing).")

        # Only set which SyncProtocol the ProcessModel implements if not 'None'
        if protocol:
            # Reset attribute on this class to not overwrite parent class
            setattr(cls, 'implements_protocol', protocol)

        return cls

    return decorate_process_model


def requires(*args: ty.Union[ty.Type[AbstractResource],
                             ty.List[ty.Type[AbstractResource]]]):
    """Decorator for ProcessModel classes that adds class variable to
    ProcessModel class that specifies which resources the ProcessModel
    requires.
    In order to express optionality between one or more resources, include
    them in a list or tuple.

    Example: @requires(Res1, Res2, [Res3, Res4])
        -> Requires Res1 and Res2 and one of Res3 or Res4
    """

    reqs = list(args)

    for req in reqs:
        if not isinstance(req, list) and not issubclass(req, AbstractResource):
            raise AssertionError("'requires' accepts individual or "
                                 "lists of 'AbstractResources'.")
        if isinstance(req, list):
            for r in req:
                if not issubclass(r, AbstractResource):
                    raise AssertionError("Lists passed to 'require' must \
                    contain subclasses of AbstractResource.")

    def decorate_process_model(cls: type):
        if not issubclass(cls, AbstractProcessModel):
            raise AssertionError("Decorated class must be a subclass "
                                 "of 'AbstractProcessModel'.")

        # Get requirements of parent class
        super_res = cls.required_resources.copy()
        # Set new requirements on this cls to not overwrite parent class
        # requirements
        setattr(cls, 'required_resources', super_res + reqs)
        return cls

    return decorate_process_model


def tags(*args: ty.Union[str, ty.List[str]]):
    """
    Decorator for ProcessModel to add a class variable (a tag-list) to
    ProcessModel class, which distinguishes between ProcessModels for same
    hardware backend and same execution language.

    For example, a user may write multiple ProcessModels in Python (
    `PyProcessModels`), requiring CPU for execution (`@requires(CPU)`). The
    compiler selects the appropriate ProcessModel via `RunConfig` using
    the keywords stored in the tag-list set by this decorator.

    The tag list is additive over inheritance. Which means, if `@tags`
    decorates a child class, whose parent is already decorated, then the new
    keywords are appended to the tag-list inherited from the parent.

    :param args: keywords that tag a ProcessModel

    Example: @requires(CPU)
             @tags('bit-accurate', 'loihi-1')
        -> these tags identify a particular ProcessModel as being
        bit-accurate with Loihi-1 hardware platform. Which means,
        the numerical output produced by such a ProcessModel on a CPU would be
        exactly same as that of Loihi-1.
    """

    arg_list = list(args)
    tag_list = []

    # Recursive function to count depth of a list
    # Ref: https://stackoverflow.com/a/30427698
    def list_depth(elem):
        return 1 + max(map(list_depth, elem), default=0) if elem and isinstance(
            elem, list) else 0

    for arg in arg_list:
        if isinstance(arg, str):
            tag_list.append(arg)
        else:
            if isinstance(arg, list) and list_depth(arg) == 1:
                tag_list.extend(arg)
            else:
                raise AssertionError("Invalid input to the 'tags' decorator. "
                                     "Valid input should be keywords as "
                                     "strings or a list of strings")

    def decorate_process_model(cls: type):
        if not issubclass(cls, AbstractProcessModel):
            raise AssertionError("Decorated class must be a subclass "
                                 "of 'AbstractProcessModel'.")
        # Check existing 'tag_list' from parent in case of sub-classing
        if hasattr(cls, 'tag_list'):
            supertags = cls.tag_list.copy()
            # Add to the parent's tag_list
            setattr(cls, 'tag_list', supertags + tag_list)
        else:
            setattr(cls, 'tag_list', tag_list)
        return cls

    return decorate_process_model
