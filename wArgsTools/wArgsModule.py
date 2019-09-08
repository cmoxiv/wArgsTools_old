from argparse import ArgumentParser, ArgumentError
import argparse
import os
import shutil
import time
import sys
import math
import inspect
import numpy as np
import pdb


class prmStruct():
    def __init__(self, **kwargs):
        self.__dict__ = kwargs
        

class wArgs(object):
    argparser = ArgumentParser(add_help=False,
                               conflict_handler='resolve',
                               fromfile_prefix_chars='@',
                               allow_abbrev=False)
    argdict = {'dummy': 0}

    def __init__(self): pass

    def prepare_args(self): pass

    @staticmethod
    def chkargs():
        wArgs.argparser.add_argument('-h', '--help', action='store_true',
                                     help='Prints argument and functionality help')
        args, unknown = wArgs.argparser.parse_known_args()

        if args.help:
            wArgs.argparser.print_help()
            exit(0)
        
        if len(unknown) > 0:
            wArgs.argparser.print_usage()
            print('Unrecognised arguments: ', *unknown)
            exit(1)
        
    @staticmethod
    def parse_args2():
        try:
            args = wArgs.argparser.parse_known_args()[0]
            wArgs.argdict.update(vars(args))
        except ArgumentError as ae:
            print(ae)
            wArgs.argparser.print_help()
            exit()

    def parse_args(self):
        try:
            self.args = self.argparser.parse_known_args()[0]
            tmpargdict = vars(self.args)
            self.argdict.update({k: v for k, v in tmpargdict.items() if ('--' + k) in sys.argv})
            return self.args

            pass
        except ArgumentError as ae:
            print(ae)
            self.argparser.print_help()
            exit()

        
class wArgsFactory():
    class Required():
        def __init__(self, argtype):
            self.argtype = argtype
            
    def __init__(self, callable, *classes, exceptions={},
                 argprfx='', argprfxexceptions=[], shortargdlm='_',
                 forceposargs=False, forcedposargs=[],
                 **globalkwargs):
        argspec = inspect.getfullargspec(callable)
        pos_args = argspec.args[:-len(argspec.kwonlydefaults)] if argspec.kwonlydefaults else argspec.args
        isclass = 'class' in str(type(callable))
        tmpposargs = pos_args[int(isclass):] + [argspec.varargs] if argspec.varargs is not None else []

        wArgsTMPBaseClass = (wArgs,) if wArgs not in inspect.getmro(callable) else ()
        
        class callablewArgs(*wArgsTMPBaseClass, callable, *classes):
            def __init__(this, *tmpposargs, **kwargs):
                wArgs.__init__(this)
                this.prepare_args()
                # pdb.set_trace()
                this.parse_args()

                # pdb.set_trace()
                this.tmpargs.update(kwargs)
                callable.__init__(this, *tmpposargs, **this.tmpargs)
                    
                for bc in classes:
                    bc.__init__(this, *tmpposargs, **kwargs)

            def chkargs(self):
                self.argparser.parse_args()
                
            def pos2kw(this, argspec, kw):
                argspec = inspect.getfullargspec(callable)
                pos_args = argspec.args[:-len(kw)]
                isclass = 'class' in str(type(callable))
                tmpposargs = pos_args[int(isclass):] + ([argspec.varargs] if argspec.varargs is not None else [])
                return {posarg: None for i, posarg in enumerate(tmpposargs) if i in forcedposargs}
                
            def prepare_args(this):
                this.argspec = inspect.getfullargspec(callable)
                tmpargparser = ArgumentParser(add_help=False,
                                              fromfile_prefix_chars='@',
                                              allow_abbrev=False)

                if this.argspec.kwonlydefaults is None:
                    if this.argspec.defaults is None:
                        this.tmpargs = {}
                        return
                    else:
                        argdef_dict = {a: d for a, d in zip(
                            this.argspec.args[-len(this.argspec.defaults):],
                            this.argspec.defaults)}
                else:
                    argdef_dict = {a: d for a, d in this.argspec.kwonlydefaults.items()}

                if forceposargs:
                    argdef_dict.update(this.pos2kw(this.argspec, argdef_dict))
                    
                this.localargparser = this.argparser.add_argument_group(callable.__name__)
                this.positional_args = this.argspec.args[:-len(argdef_dict)]
                this.keyword_names = this.argspec.args[-len(argdef_dict):]

                for arg, default in argdef_dict.items():
                    thisargprfx = '' if arg in argprfxexceptions else argprfx
                    argname = '--{prfx}{arg}'.format(prfx=thisargprfx, arg=arg)
                    argdest = arg
                    
                    argdef = default
                    argtype = type(default)  # if default is not None else float

                    if arg in exceptions.keys():
                        argtype = exceptions[arg]
                        
                    if argname == '--defaults':
                        continue

                    if argtype.__name__ in ['Required']:
                        apkw = {'Required': {'required': True, 'type': argdef.argtype}}

                    elif argtype.__name__ in ['list', 'tuple']:  # iterables
                        apkw = {'list': {'type': type(argdef[0]),
                                         'nargs': len(argdef)} if len(argdef) else {'nargs': '+'},
                                'tuple': {'type': type(argdef[0]),
                                          'nargs': len(argdef)} if len(argdef) else {'nargs': '+'}}
                                
                    else:
                        apkw = {'bool': {'action': 'store_true'},
                                'NoneType': {}}

                    if argtype.__name__ in apkw.keys():
                        this.localargparser.add_argument(argname, default=argdef,
                                                         **apkw[argtype.__name__])
                        tmpargparser.add_argument(argname, default=argdef,
                                                  **apkw[argtype.__name__])
                    else:
                        this.localargparser.add_argument(argname, type=argtype,
                                                         default=argdef)
                        tmpargparser.add_argument(argname, type=argtype,
                                                  default=argdef)

                this.tmpargs = vars(tmpargparser.parse_known_args()[0])

                NoneKeys = [k for k, v in argdef_dict.items() if v is None and forceposargs]
                for k in NoneKeys:
                    this.tmpargs[k] = eval(this.tmpargs[k]) if this.tmpargs[k] is not None else None

                if len(argprfx):
                    tmptmpargs = {argprfx.join(k.split(argprfx)[1:]): v
                                  for k, v in this.tmpargs.items() if argprfx in k}
                    tmptmpargs.update({k: v for k, v in this.tmpargs.items() if argprfx not in k})
                    this.tmpargs = tmptmpargs

        self.callable = callablewArgs
        self.callable.__name__ = '{}_wArgs'.format(callable.__name__)
