"""
simuPOP utilities.

This module provides some commonly used operators
and format conversion utilities.

"""

import exceptions, operator, types, os, sys, getopt, re, math

from simuPOP import *

def _listVars(var, level=-1, name='', subPop=True, indent=0, curLevel=0):
  ''' called by listVars. Will list variables recursively'''
  if type(var) == type( dw({}) ):
    var = var.__dict__
  # all level or level < specified maximum level
  if level < 0 or (level > 0 and curLevel < level):
    # list is list or typle type
    if type(var) == types.ListType or type(var) == types.TupleType:
      index = 0
      for x in var:
        # literals
        if type(x) != types.ListType and type(x) != types.DictType:
          # this will save a huge amount of output for sparse matrix
          # generated by Stat(LD=[]) etc.
          if x != None: 
            if type(var) == types.ListType:
              print ' '*indent, '['+str(index)+']\t', x
            else:
              print ' '*indent, '('+str(index)+')\t', x
        # nested stuff
        elif type(x) == types.ListType or type(x) == types.DictType:
          if type(var) == types.ListType:
            print ' '*indent, '['+str(index)+']\n',
          else:
            print ' '*indent, '('+str(index)+')\n',
          _listVars(x, level, name, False, indent+2, curLevel + 1)
        index += 1      
    elif type(var) == types.DictType:
      # none array first
      for x in var.items():
        if not type(x[1]) in [types.ListType, types.DictType, types.TupleType]:
          if name == '' or x[0] == name:
            print ' '*indent, x[0], ':\t', x[1]
      # array but not subPop
      for x in var.items():
        if x[0] != 'subPop' and type(x[1]) in [types.ListType, types.DictType, types.TupleType]:
          if name == '' or x[0] == name:
            print ' '*indent, x[0], ':\n',
            _listVars(x[1], level, name, False, indent+2, curLevel + 1)
      # subPop
      if subPop == True and var.has_key('subPop'):
        print ' '*indent, 'subPop\n',
        _listVars(var['subPop'], level, name, False, indent+2, curLevel + 1)
    else:
      print ' '*indent, var
  else: # out of the range of level
    if type(var) == types.ListType or type(var) == types.TupleType:
      print ' '*indent, 'list of length', len(var)
    elif type(var) == types.DictType:
      print ' '*indent, 'dict with keys [',
      for num in range(0,len(var.keys())):
        if type(var.keys()[num]) == types.StringType:
          print "'"+ var.keys()[num] + "',",
        else:
          print var.keys()[num], ",",
        if num != len(var.keys())-1 and num%4 == 3:
          print '\n' + ' '*(indent+5),
      print ']'
    else:
      print ' '*indent, var

def listVars(var, level=-1, name='', subPop=True, useWxPython=True):
  ''' 
    list a variable in tree format, either in text format or in a 
      wxPython window.
    
    var:    any variable to be viewed. Can be a dw object returned
            by dvars() function
    level:  level of display.
    name:   only view certain variable
    subPop: whether or not display info in subPop
    useWxPython: if True, use terminal output even if wxPython is available.
  '''
  if not useWxPython:
    _listVars(var, level, name, subPop, 0, 0)
    return 

  # a wxPython version of listVars
  try:
    import wx, wx.py.filling as fill
  except:
    _listVars(var, level, name, subPop, 0, 0)
    return

  app = wx.App()
  wx.InitAllImageHandlers()
  if var==None:
    fillFrame = fill.FillingFrame()
  else:
    if type(var) == type( dw({}) ):
      fillFrame = fill.FillingFrame(rootObject=var.__dict__,
        rootLabel='var')
    else:
      fillFrame = fill.FillingFrame(rootObject=var,
        rootLabel='var')        
  fillFrame.Show(True)
  app.SetTopWindow(fillFrame)
  app.MainLoop()


#
# demographic changes
def constSize(size, split=0, numSubPop=1, bottleneckGen=-1, bottleneckSize=0):
  ''' The population size is constant, but will split into
    numSubPop subpopulations at generation split
  '''
  def func(gen, oldSize=[]):
    if gen == bottleneckGen:
      if gen < split:
        return [bottleneckSize]
      else:
        return [int(bottleneckSize/numSubPop)]*numSubPop
    # not bottleneck
    if gen < split:
      return [size]
    else:
      return [int(size/numSubPop)]*numSubPop
  return func

def LinearExpansion(initSize, endSize, end, burnin=0, split=0, numSubPop=1, bottleneckGen=-1, bottleneckSize=0):
  ''' Linearly expand population size from intiSize to endSize
    after burnin, split the population at generation split.
  '''
  inc = (endSize-initSize)/float(end-burnin)
  def func(gen, oldSize=[]):
    if gen == bottleneckGen:
      if gen < split:
        return [bottleneckSize]
      else:
        return [bottleneckSize/numSubPop]*numSubPop
    # not bottleneck
    if gen <= burnin:
      tot = initSize
    else:
      tot = initSize + inc*(gen-burnin)
    #
    if gen < split:
      return [int(tot)]
    elif gen > end:
      return [int(endSize/numSubPop)]*numSubPop
    else:
      return [int(tot/numSubPop)]*numSubPop
  return func

def ExponentialExpansion(initSize, endSize, end, burnin=0, split=0, numSubPop=1, bottleneckGen=-1, bottleneckSize=0):
  ''' Exponentially expand population size from intiSize to endSize
    after burnin, split the population at generation split.
  '''
  rate = (math.log(endSize)-math.log(initSize))/(end-burnin)
  def func(gen, oldSize=[]):
    if gen == bottleneckGen:
      if gen < split:
        return [bottleneckSize]
      else:
        return [bottleneckSize/numSubPop]*numSubPop
    # not bottleneck
    if gen <= burnin:
      tot = initSize
    else:
      tot = int(initSize*math.exp((gen-burnin)*rate))
    if gen < split:
      return [int(tot)]
    elif gen > end:
      return [int(endSize/numSubPop)]*numSubPop
    else:
      return [int(tot/numSubPop)]*numSubPop
  return func

def InstantExpansion(initSize, endSize, end, burnin=0, split=0, numSubPop=1, bottleneckGen=-1, bottleneckSize=0):
  '''  Instaneously expand population size from intiSize to endSize
    after burnin, split the population at generation split.
  '''
  def func(gen, oldSize=[]):
    if gen == bottleneckGen:
      if gen < split:
        return [bottleneckSize]
      else:
        return [bottleneckSize/numSubPop]*numSubPop
    # not bottleneck
    if gen <= burnin:
      tot = initSize
    else:
      tot = endSize
    if gen < split:
      return [int(tot)]
    else:
      return [int(tot/numSubPop)]*numSubPop    
  return func

# for internal use only
def testDemoFunc(end, func):
  g = range(end)
  rng = [min( [ func(x)[0] for x in g]), 
      max( [ sum(func(x)) for x in g])]
  r.plot(g, [sum(func(x)) for x in g], ylim=rng, type='l', xlab='gen', ylab='subPopSize(0)')
  r.lines(g, [func(x)[0] for x in g], type='l', xlab='gen', ylab='subPopSize(0)', lty=2)

# migration rate matrix generators
def migrIslandRates(r, n):
  '''
   migration rate matrix

   x m/(n-1) m/(n-1) ....
   m/(n-1) x ............
   .....
   .... m/(n-1) m/(n-1) x
   
  where x = 1-m
  '''
  # n==1?
  if n == 1:
    return [[1]]
  #
  m = []
  for i in range(0,n):
    m.append( [r/(n-1.)]*n)
    m[-1][i] = 1-r
  return m             
  

def migrSteppingStoneRates(r, n, circular=False):
  '''
   migration rate matrix, circular step stone model (X=1-m)
  
   X   m/2               m/2
   m/2 X   m/2           0
   0   m/2 x   m/2 ......0
   ...
   m/2 0 ....       m/2  X

   or non-circular
  
   X   m/2               m/2
   m/2 X   m/2           0
   0   m/2 X   m/2 ......0
   ...
   ...              m   X
  ''' 
  if n < 2: 
    raise exceptions.ValueError("Can not define step stone model for n < 2")
  elif n == 2:
    return [[1-r,r],[r,1-r]]
  # the normal case (n>2)
  m = []
  for i in range(0, n):
    m.append([0]*n)
    m[i][i] = 1-r
    m[i][(i+1)%n] = r/2.
    m[i][(i+n-1)%n] = r/2.
  if not circular:
    m[0][1] = r
    m[0][-1] = 0
    m[n-1][0] = 0
    m[n-1][n-2] = r
  return m

  
# if you do not like the internal Fst (Weir & Cockerham, Fstat)
# you can calculate Fst from heterozygosities
# (this is more like an example of pure-python statistics)
#
# This function ( and the following operator) depends on simuPOP's
# basicStat to provide observed and expected heterozygosity.
#
# Calls to calc_hetero_H and hetero_H should be preceded by call to
#   basicStat(hetero=[ loci]
#
# the first parameter allele takes the form
#  [[locus allele1 allele2 ], [locus2, allele1, allele2...]]
# just like what is in basicStat(Fst=...)
def calc_Fst_H(pop, alleles):
  """ calculate expected heterozygosities at given loci
    Formula etc please refer to user's manual
  """
  s = pop.dvars()
  if len(alleles) == 0:
    raise exceptions.ValueError("Please specify alleles on which to calculate Fst_H")
  
  for l in alleles:   # of form [locus, allele, allele ...]
    if (type(l) != type([]) and type(l) != type(())) or len(l) <= 1:
      raise exceptions.ValueError("Format [ [ locus, allele,...]. [...] ]");
    
    s.Fst_H = {}
    s.Fis_H = {}
    s.Fit_H = {}
    loc = l[0]
    for ale in l[1:]:
      # calculate Fst_H for each loc, ale pair.
      # H_I based on observed heterozygosities in individuals in subpopulations
      H_I = 0.0
      H_S = 0.0
      for sp in range(0, s.numSubPop):
        H_I = H_I + s.subPopSize[sp]*s.subPop[sp]['heteroFreq'][loc][ale]
        H_S = H_S + s.subPopSize[sp]*s.subPop[sp]['heteroFreq'][loc][0]
      H_I = H_I / s.popSize
      H_S = H_S / s.popSize
      H_T = s.heteroFreq[loc][0]
      s.Fst_H['%d-%d' % (loc,ale)] = (H_T - H_S)/H_T
      s.Fis_H['%d-%d' % (loc,ale)] = (H_S - H_I)/H_S
      s.Fit_H['%d-%d' % (loc,ale)] = (H_T - H_I)/H_T


# the operator wrapper of calc_hetero
def Fst_H(alleles,**kwargs):
  parm = ''  
  for (k,v) in kwargs.items():
    parm += ' , ' + str(k) + '=' + str(v)
  #  calc_Fst_H(loci= loci?, rep=rep)
  cmd = r'pyExec( exposePop=1, stmts=r"""calc_Fst_H(pop=pop, alleles= ' + \
    str(alleles) + ')""", %s)' % parm
  # print cmd
  return eval( cmd )

# 
# operator tab (I can use operator output
# but the name conflicts with parameter name
# and I would not want to go through the trouble
# of a walkaround (like aliasing output)
def tab(output=">", outputExpr="", **kwargs):
  parm = ''  
  for (k,v) in kwargs.items():
    parm += ' , ' + str(k) + '=' + str(v)
  cmd = r'''pyEval( r'"\t"' ''' + ', output="""' + output + \
    '""", outputExpr="""' + outputExpr + '"""' + parm + ')'
  # print cmd
  return eval(cmd)

def endl(output=">", outputExpr="", **kwargs):
  parm = ''  
  for (k,v) in kwargs.items():
    parm += ' , ' + str(k) + '=' + str(v)
  cmd = r'''pyEval( r'"\n"' ''' + ', output="""' + output + \
    '""", outputExpr="""' + outputExpr + '"""' + parm + ')'
  # print cmd
  return eval(cmd)


# aggregator
# used by varPlotters
class Aggregator:
  """
  collect variables so that plotters can
  plot them all at once
  
  """
  def __init__(self, win=0, width=0):
    """
    win: window size. I.e., maximum generations of data to keep
    """
    self.gen = []
    self.data = []
    self.win = win
    self.width = width
  
  def __repr__(self):
    s = str(self.gen) + "\n"
    for i in range(0, len(self.data)):
      s += str(self.data[i]) + "\n"
    return s

  def clear(self):
    self.gen = []
    self.data = []
   
  def ylim(self):
    if len(self.gen) == 0:
      return [0,0]

    y0 = self.data[0][0]
    y1 = self.data[0][0]

    for i in range(0, len(self.data)):
      for j in range(0, len(self.data[i])):
        if self.data[i][j] < y0:
          y0 = self.data[i][j]
        if self.data[i][j] > y1:
          y1 = self.data[i][j]
    return [y0,y1]

  def flatData(self):
    fd = carray('d',[])
    for i in range(0, self.width):
      fd += self.data[i]
    return fd
    
  def push(self, _gen, _data, _idx=-1 ):
    # first add data to allData
    if self.width == 0 and _idx != -1:
      raise exceptions.ValueError("You can not store items one by one if width is not specified")
    
    if self.width == 0:   # _idx != -1, _data is an array,
      self.width = len(_data)
      for i in range(0, self.width):
        self.data.append( carray('d', [_data[i]]))
      self.gen = carray('i', [ _gen ])        
      return
    
    # self.width is not zero.
    if _idx == -1:    # given an array
      if len(_data) != self.width:
        raise exceptions.ValueError, "data should have the same length"
      if len(self.gen) == 0:    # first time.
        for i in range(0, self.width):
          self.data.append( carray('d', [_data[i]]))
        self.gen = carray('i', [ _gen ])
      else:   # append data
        for i in range(0, self.width):
          self.data[i] += carray('d', [_data[i]])
        self.gen += carray('i', [ _gen ])
      
    else:     # _idx != -1 , given a number
      if type(_data) == type(()) or type(_data) == type([]) :
        raise exceptions.ValueError("If idx is specified, _data should not be a list.")
        
      if _idx >= self.width:
        raise exceptions.IndexError("Index out of range")
          
      if len(self.gen) == 0:  # first time
        self.gen = carray('i', [_gen])
        for i in range(0, self.width):
          self.data.append( carray('d', [0]) )
        self.data[0][_idx] = _data
      else:   # append
        if self.gen[-1] == _gen:   # alreay exist
          self.data[_idx][-1] = _data
          return 
        else:
          self.gen += carray('i', [_gen])
          for i in range(0, self.width):
            self.data[i] += carray('d', [0]) 
          self.data[_idx][-1] = _data
     
    # trim data if necessary
    if self.win > 0 :
      if self.gen[-1] - self.gen[0] > self.win:
        self.gen = self.gen[1:]
        for i in range(0, self.width):
          self.data[i] = self.data[i][1:]


# data collector
#
def CollectValue(pop, gen, expr, name):
  value = eval(expr, globals(), pop.vars())
  d = pop.vars()
  if not d.has_key(name):
    d[name] = {}
  d[name][gen] = value

# wrapper
def collector(name, expr, **kwargs):
  # deal with additional arguments
  parm = ''
  for (k,v) in kwargs.items():
    parm += str(k) + '=' + str(v) + ', '
  # pyEval( exposePop=1, param?, stmts="""
  # Collect(pop, expr, name)
  # """)
  opt = '''pyExec(exposePop=1, %s
    stmts=r\'\'\'CollectValue(pop, gen,
      expr="""%s""", name="""%s""")\'\'\')''' \
    % ( parm, expr, name) 
  #print opt
  return eval(opt)
  
# save file in FSTAT format   
def SaveFstat(pop, output='', outputExpr='', maxAllele=0):
  if output != '':
    file = output
  elif outputExpr != '':
    file = eval(outputExpr, globals(), pop.vars() )
  else:
    raise exceptions.ValueError, "Please specify output or outputExpr"
  # open file
  try:
    f = open(file, "w")
  except exceptions.IOError:
    raise exceptions.IOError, "Can not open file " + file + " to write."
  #  
  # file is opened.
  np = pop.numSubPop()
  if np > 200:
    print "Warning: Current version (2.93) of FSTAT can not handle more than 200 samples"
  nl = pop.totNumLoci()
  if nl > 100:
    print "Warning: Current version (2.93) of FSTAT can not handle more than 100 loci"
  if maxAllele != 0:
    nu = maxAllele
  else:
    nu = pop.maxAllele()
  if nu > 999:
    print "Warning: Current version (2.93) of FSTAT can not handle more than 999 alleles at each locus"
    print "If you used simuPOP_la library, you can specify maxAllele in population constructure"
  if nu < 10:
    nd = 1
  elif nu < 100:
    nd = 2
  elif nu < 1000:
    nd = 3
  else: # FSTAT can not handle this now. how many digits?
    nd = len(str(nu))
  # write the first line
  f.write( '%d %d %d %d\n' % (np, nl, nu, nd) )
  # following lines with loci name.
  for loc in range(0, pop.totNumLoci()):
    f.write( pop.locusName(loc) +"\n");
  gs = pop.totNumLoci()
  for sp in range(0, pop.numSubPop()):
    # genotype of subpopulation sp, individuals are
    # rearranged in perfect order
    gt = pop.arrGenotype(sp)
    for ind in range(0, pop.subPopSize(sp)):
      f.write("%d " % (sp+1))
      p1 = 2*gs*ind        # begining of first hemo copy
      p2 = 2*gs*ind + gs   # second
      for al in range(0, gs): # allele
        ale1 = gt[p1+al]
        ale2 = gt[p2+al]
        if ale1 == 0 or ale2 == 0:
          f.write('%%%dd' % (2*nd) % 0 )
        else:
          f.write('%%0%dd%%0%dd ' % (nd, nd) % (ale1, ale2))
      f.write( "\n")
  f.close()  

# operator version of the function SaveFstat
def saveFstat(output='', outputExpr='', **kwargs):
  # deal with additional arguments
  parm = ''
  for (k,v) in kwargs.items():
    parm += str(k) + '=' + str(v) + ', '
  # pyEval( exposePop=1, param?, stmts="""
  # saveInFSTATFormat( pop, rep=rep?, output=output?, outputExpr=outputExpr?)
  # """)
  opt = '''pyEval(exposePop=1, %s
    stmts=r\'\'\'SaveFstat(pop, rep=rep, output=r"""%s""", 
    outputExpr=r"""%s""" )\'\'\')''' % ( parm, output, outputExpr) 
  # print opt
  return eval(opt)

# used to parse name
import re

# load population from fstat file 'file'
# since fstat does not have chromosome structure
# an additional parameter can be given
def LoadFstat(file, loci=[]):
  # open file
  try:
    f = open(file, "r")
  except exceptions.IOError:
    raise exceptions.IOError("Can not open file " + file + " to read.")
  #  
  # file is opened. get basic parameters
  try:
    # get numSubPop(), totNumLoci(), maxAllele(), digit
    [np, nl, nu, nd] = map(int, f.readline().split())
  except exceptions.ValueError:
    raise exceptions.ValueError("The first line does not have 4 numbers. Are you sure this is a FSTAT file?")
  
  # now, ignore nl lines, if loci is empty try to see if we have info here
  # following lines with loci name.
  numLoci = loci
  lociNames = []
  if loci != []: # ignore allele name lines
    if nl != reduce(operator.add, loci):
      raise exceptions.ValueError("Given number of loci does not add up to number of loci in the file")
    for al in range(0, nl):
      lociNames.append(f.readline().strip() )
  else:
    scan = re.compile(r'\D*(\d+)\D*(\d+)')
    for al in range(0, nl):
      lociNames.append( f.readline().strip())
      # try to parse the name ...
      try:
        #print "mating ", lociNames[-1]
        ch,loc = map(int, scan.match(lociNames[-1]).groups())
        # get numbers?
        #print ch, loc
        if len(numLoci)+1 == ch:
          numLoci.append( loc )
        else:
          numLoci[ ch-1 ] = loc
      except exceptions.Exception:
        pass
    # if we can not get numbers correct, put all loci in one chromosome
    if reduce(operator.add, numLoci, 0) != nl:
      numLoci = [nl]
  #
  # now, numLoci should be valid, we need number of population
  # and subpopulations
  maxAllele = 0
  gt = []
  for line in f.readlines():
    gt.append( line.split() )
  f.close()
  # subpop size?
  subPopIndex = map(lambda x:int(x[0]), gt)
  # count subpop.
  subPopSize = [0]*subPopIndex[-1]
  for i in range(0, subPopIndex[-1]):
    subPopSize[i] = subPopIndex.count(i+1)
  if len(subPopSize) != np:
    raise exceptions.ValueError("Number of subpop does not match")
  if reduce(operator.add, subPopSize) != len(gt):
    raise exceptions.ValueError("Population size does not match")
  # we have all the information, create a population
  pop = population( subPop=subPopSize, loci = numLoci, ploidy=2,
    lociNames=lociNames)
  # 
  gs = pop.totNumLoci()
  popGT = pop.arrGenotype()
  for ind in range(0, len(gt)):
    p1 = 2*gs*ind        # begining of first hemo copy
    p2 = 2*gs*ind + gs   # second
    for al in range(0, gs): # allele
      ale = int(gt[ind][al+1])
      popGT[2*gs*ind + al] = ale/(10**nd)
      popGT[2*gs*ind + gs + al] = ale%(10*nd)
      if popGT[2*gs*ind + al] > maxAllele:
        maxAllele = popGT[2*gs*ind + al]
      if popGT[2*gs*ind + gs + al] > maxAllele:
        maxAllele = popGT[2*gs*ind + gs + al]
  pop.setMaxAllele(maxAllele)
  return pop

# read GC data file in http://wpicr.wpic.pitt.edu/WPICCompGen/genomic_control/genomic_control.htm
def LoadGCData(file, loci=[]):
  # open file
  try:
    f = open(file, "r")
  except exceptions.IOError:
    raise exceptions.IOError("Can not open file " + file + " to read.")
  gt = []
  for line in f.readlines():
    gt.append( line.split() )
  f.close()
  # now we have a 2-d matrix of strings
  # population size?
  popSize = len(gt)
  # number of alleles
  numAllele = (len(gt[0]))/2-1
  #
  # loci number
  if reduce(operator.add, loci,0.) == numAllele:
    lociNum = loci
  else:
    lociNum = [numAllele]
  # create population
  pop = population(size=popSize, ploidy=2, loci=lociNum, maxAllele=2)
  # 
  gs = pop.totNumLoci()
  popGT = pop.arrGenotype()
  for ind in range(0, len(gt)):
    pop.individual(ind).setAffected( int(gt[ind][1]))
    p1 = 2*gs*ind        # begining of first hemo copy
    p2 = 2*gs*ind + gs   # second
    for al in range(0, gs): # allele
      popGT[2*gs*ind + al] = int(gt[ind][al*2+2])
      popGT[2*gs*ind + gs + al] = int(gt[ind][al*2+3])
  return pop


#    
def SaveLinkage(pop, popType='sibpair', output='', outputExpr='', alleleFreq=[], 
   recombination=0.001, chrom=[], exclude=[], pre=True, daf=0.001):
  """ save population in Linkage format. Currently only
    support affected sibpairs sampled with affectedSibpairSample
    operator.
     
    pop: population to be saved. Must have ancestralDepth 1.
      paired individuals are sibs. Parental population are corresponding
      parents.

    popType: population type. Can be 'sibpair' or 'bySubPop'. If type is sibpair,
      pairs of individuals will be considered as sibpairs. If type is bySubPop,
      individuals in a subpopulation is considered as siblings.
    
    output: output.dat and output.ped will be the data and pedigree file.
      You may need to rename them to be analyzed by LINKAGE. This allows
      saving multiple files.
      
    outputExpr: expression version of output.

    chrom: only save these chromosomes

    exclude: exclude some loci
    
    pre: True. pedigree format to be fed to makeped
    
    Note:
      the first child is always the proband.
  """
  if output != '':
    file = output
  elif outputExpr != '':
    file = eval(outputExpr, globals(), pop.vars() )
  else:
    raise exceptions.ValueError, "Please specify output or outputExpr"
  # open data file and pedigree file to write.
  try:
    dataFile = open(file + ".dat", "w")
    pedFile = open(file + ".ped", "w")
  except exceptions.IOError:
    raise exceptions.IOError, "Can not open file " + file + ".dat/.ped to write."
  if chrom == []:
    chs = range(0, pop.numChrom())
  elif type(chrom) == type(1):
    chs = [chrom]
  else:
    chs = chrom
  numLoci = 0
  realExclude = []
  for ch in chs:
    numLoci += pop.numLoci(ch)
    # look at excluded loci, are they in this chrom?
    for e in exclude:
      if e >= pop.chromBegin(ch) and e < pop.chromEnd(ch):
        realExclude.append(e)
  #  
  # file is opened.
  # write data file
  # nlocus
  # another one is affection status 
  dataFile.write( str( numLoci + 1 - len(realExclude) ) + " ")
  # risklocus (not sure. risk is not to be calculated)
  dataFile.write( '0 ' )
  # sexlink autosomal: 0
  dataFile.write( '0 ')
  # nprogram whatever
  dataFile.write( '5 << nlocus, risklocus, sexlink, nprogram\n')
  # mutsys: all loci are mutational? 0 right now
  dataFile.write( '0 ')
  # mutmale
  dataFile.write( '0 ')
  # mutfemale
  dataFile.write( '0 ')
  # disequil: assume in LD? Yes.
  dataFile.write( '0 << mutsys, mutmale, mutfemale, disequil\n')
  # order of loci
  string = ''
  for m in range(0, numLoci - len(realExclude)):
    string += "%d " % (m + 1)
  dataFile.write( string + " << order of loci\n")
  # describe affected status
  dataFile.write( "1 2 << affection status code, number of alleles\n")
  dataFile.write( "%f %f << gene frequency\n" % ( 1-daf, daf) )
  dataFile.write( "1 << number of factors\n")
  dataFile.write( "0 0.4 .8 << penetrance\n")
  # describe each locus
  if alleleFreq == []: # if not given,
    print "Warning: using sample allele frequency."
    Stat(pop, alleleFreq=range(0, pop.totNumLoci()))
    af = pop.dvars().alleleFreq
  else:
    af = alleleFreq
  for ch in chs:
    for m in range(0, pop.numLoci(ch)):
      marker = pop.chromBegin(ch) + m
      if marker in realExclude:
        continue
      # now, 3 for numbered alleles
      numAllele = len(af[marker])-1
      dataFile.write( '3 %d << numbered alleles code, totl number of alleles \n' % numAllele )
      # allele frequency
      string = ''
      for ale in range(1, numAllele+1):
        string += '%.6f ' % af[marker][ale]
      dataFile.write( string + ' << gene frequencies \n')
  # sex-difference
  dataFile.write('0 ')
  # interference
  dataFile.write('0 << sex difference, interference\n')
  # recombination: I have mutliple chromosome!
  string = str(recombination) + ' '  # this one is for affection status
  for ch in chs:
    for m in range(1, pop.numLoci(ch)):
      if not pop.chromBegin(ch) + m in realExclude:
        string += '%f ' % recombination
    if ch != chs[len(chs)-1]:
      string += '.5 '
  dataFile.write( string + ' << recombination rates \n ')
  dataFile.write( "1 0.1 0.1\n")
  # done!
  dataFile.close()
  # write pedigree file (affected sibpairs)
  # sex: in linkage, male is 1, female is 2
  def sexCode(ind):
    if ind.sex() == Male:
      return 1
    else:
      return 2
  # disease status: in linkage affected is 2, unaffected is 1
  def affectedCode(ind):
    if ind.affected():
      return 2
    else:
      return 1
  # alleles string
  # determine which markers will be used.
  markers = {}
  for ch in chs:
    markers[ch] = []
    for m in range(0, pop.numLoci(ch)):
      marker = pop.chromBegin(ch) + m
      if not marker in realExclude:
        markers[ch].append(marker)
  def genoStr(ind):
    string = ''
    for ch in chs:
      for marker in markers[ch]:
        string += "%d %d " % (ind.allele(marker, 0), ind.allele(marker, 1))
    return string
  if popType == "sibpair":
    # number of pedigrees
    np = pop.popSize()/2
    for ped in range(0, np):
      # get parent
      pop.useAncestralPop(1)
      # pedigree number, individual ID, dad, mom, first os
      # next parental sib, maternal sib, sex, proband, disease status
      par1 = pop.individual(2*ped)
      if pre:
        pedFile.write("%3d 1 0 0 %d %d " \
          % (ped+1, sexCode(par1), affectedCode(par1)))
      else:
        pedFile.write("%3d 1 0 0 3 0 0 %d 0 %d " \
          % (ped+1, sexCode(par1), affectedCode(par1)))
      pedFile.write( genoStr(par1) + '\n' )
      par2 = pop.individual(2*ped+1)
      if pre:
        pedFile.write("%3d 2 0 0 %d %d " \
          % (ped+1, sexCode(par2), affectedCode(par2)))
      else:
        pedFile.write("%3d 2 0 0 3 0 0 %d 0 %d " \
          % (ped+1, sexCode(par2), affectedCode(par2)))
      pedFile.write( genoStr(par2) + '\n' )
      # dealing with offspring
      if par1.sex() == Male:
        dadID = 1
        momID = 2
      else:
        dadID = 2
        momID = 1
      pop.useAncestralPop(0)
      # pedigree number, individual ID, dad, mom, first os
      # next parental sib, maternal sib, sex, proband, disease status
      off1 = pop.individual(2*ped)
      if pre:
        pedFile.write("%3d 3 %d %d %d %d " \
          % (ped+1, dadID, momID, sexCode(off1), affectedCode(off1)))
      else:
        pedFile.write("%3d 3 %d %d 0 4 4 %d 1 %d " \
          % (ped+1, dadID, momID, sexCode(off1), affectedCode(off1)))
      pedFile.write( genoStr(off1) + '\n' )
      off2 = pop.individual(2*ped+1)
      if pre:
        pedFile.write("%3d 4 %d %d %d %d " \
          % (ped+1, dadID, momID, sexCode(off2), affectedCode(off2)))
      else:
        pedFile.write("%3d 4 %d %d 0 0 0 %d 0 %d " \
          % (ped+1, dadID, momID, sexCode(off2), affectedCode(off2)))
      pedFile.write( genoStr(off2) + '\n' )
  elif popType == 'bySubPop': # pop type is bySubPop
    # number of pedigrees
    np = pop.numSubPop()
    offset = 0
    for ped in range(0, np):
      # ignore empty subpops
      if pop.subPopSize(ped) == 0:
        continue
      # using what index?
      # if ped 0 is not empty... this guarantees that there is no 0 family ID
      if ped == 0:  
        offset = 1
      # get parent
      pop.useAncestralPop(1)
      # pedigree number, individual ID, dad, mom, first os
      # next parental sib, maternal sib, sex, proband, disease status
      if pop.subPopSize(ped) > 2:
        raise exceptions.ValueError("Pedigree " + str(ped) + " has more than two parents.")
      famID = 1
      if pop.subPopSize(ped) >= 1:
        par1 = pop.individual(0, ped)
        if pre:
          pedFile.write("%3d %d 0 0 %d %d " \
            % (ped+offset, famID, sexCode(par1), affectedCode(par1)))
        else:
          pedFile.write("%3d %d 0 0 3 0 0 %d 0 %d " \
            % (ped+offset, famID, sexCode(par1), affectedCode(par1)))
        pedFile.write( genoStr(par1) + '\n' )
        famID += 1
      if pop.subPopSize(ped) == 2:    # if there are two parents 
        par2 = pop.individual(1,ped)
        par2sex = sexCode(par2)
        if sexCode(par1) == par2sex:
          print "Warning: same sex parents at pedigree " + str(ped) 
          if sexCode(par1) == Male:
            par2sex = Female
          else:
            par2sex = Male
        if pre:
          pedFile.write("%3d %d 0 0 %d %d " \
            % (ped+offset, famID, par2sex, affectedCode(par2)))
        else:
          pedFile.write("%3d %d 0 0 3 0 0 %d 0 %d " \
            % (ped+offset, famID, par2sex, affectedCode(par2)))
        pedFile.write( genoStr(par2) + '\n' )
        famID += 1
      # dealing with offspring
      if famID == 1: # no parents
        dadID = 0
        momID = 0
      elif famID == 2: # one parent
        if par1.sex() == Male:
          dadID = 1
          monID = 0
        else:
          dadID = 0
          monID = 1
      else: # two parents
        if par1.sex() == Male:
          dadID = 1
          momID = 2
        else:
          dadID = 2
          momID = 1
      pop.useAncestralPop(0)
      # pedigree number, individual ID, dad, mom, first os
      # next parental sib, maternal sib, sex, proband, disease status
      #
      # can have many offsprings
      for o in range(0, pop.subPopSize(ped)):
        off = pop.individual(o,ped)
        if pre:
          pedFile.write("%3d %d %d %d %d %d " \
            % (ped+offset, famID, dadID, momID, sexCode(off), affectedCode(off)))
        else:
          pedFile.write("%3d %d %d %d 0 4 4 %d 1 %d " \
            % (ped+offset, famID, dadID, momID, sexCode(off), affectedCode(off)))
        pedFile.write( genoStr(off) + '\n' )
        famID += 1
  else:
    raise exceptions.ValueError("Only popType 'sibpair' and 'bySubPop' are supported.")
  # close all files
  pedFile.close()  

# operator version of saveLinkage
def saveLinkage(output='', outputExpr='', **kwargs):
  "An operator to save population in linkage format"
  # deal with additional arguments
  parm = ''
  for (k,v) in kwargs.items():
    parm += str(k) + '=' + str(v) + ', '
  # pyEval( exposePop=1, param?, stmts="""
  # saveInFSTATFormat( pop, rep=rep?, output=output?, outputExpr=outputExpr?)
  # """)
  opt = '''pyEval(exposePop=1, %s
    stmts=r\'\'\'SaveLinkage(pop, rep=rep, output=r"""%s""", 
    outputExpr=r"""%s""" )\'\'\')''' % ( parm, output, outputExpr) 
  # print opt
  return eval(opt)



def SaveCSV(pop, output='', outputExpr='', exclude=[], **kwargs):
  """ save file in CSV format 
  This format is used mostly for randTent method.
  Ihe format is:
  
    chromsome #,,,locusName,locusDist,locusName,locusDist,....
    famID,indID,sex,affectedness,allel1-1,allel1-2,allele2-1,allele2-2,
    ...
    ...
    chromosome # ....
    
  """
  if output != '':
    file = output
  elif outputExpr != '':
    file = eval(outputExpr, globals(), pop.vars() )
  else:
    raise exceptions.ValueError, "Please specify output or outputExpr"
  markers = {}
  for ch in range(0,pop.numChrom()):
    markers[ch] = []
    for m in range(0, pop.numLoci(ch)):
      if not pop.chromBegin(ch) + m in exclude:
        # record relative location, not excluded
        markers[ch].append(m)
  try:
    out = open( file, "w")
  except exceptions.IOError:
    raise exceptions.IOError, "Can not open file " + file +" to write."
  # keep the content of pieces in strings first
  content = [''] * pop.numChrom()
  for i in range(0, pop.numChrom()):
    content[i] +=  'Chromosome ' + str(i+1) + ',,,'
    for m in markers[i]:
      content[i] += ",locus%d_%d,%d" % (i+1, m+1, m+1)
    content[i] += "\n"
  # for each family
  def sexCode(ind):
    if ind.sex() == Male:
      return 1
    else:
      return 2
  # disease status: in linkage affected is 2, unaffected is 1
  def affectedCode(ind):
    if ind.affected():
      return 1
    else:
      return 2
  # alleles string
  def genoStr(ind, ch):
    string = ''
    for marker in markers[ch]:
      string += ",%d,%d" % (ind.allele(marker, 0, ch), ind.allele(marker, 1, ch))
    return string
  # number of pedigrees
  np = pop.popSize()/2
  # offspring ID start with popSize.
  for ch in range(0, pop.numChrom()):
    for ped in range(0, np):
      # get parent
      pop.useAncestralPop(1)
      # pedigree number, individual ID, dad, mom, first os
      # next parental sib, maternal sib, sex, proband, disease status
      par1 = pop.individual(2*ped)
      content[ch] += "%3d,1,%d,%d" % (ped+1, sexCode(par1), affectedCode(par1))
      content[ch] +=  genoStr(par1, ch) + '\n' 
      par2 = pop.individual(2*ped+1)
      content[ch] += "%3d,2,%d,%d" % (ped+1, sexCode(par2), affectedCode(par2))
      content[ch] +=  genoStr(par2, ch) + '\n' 
      pop.useAncestralPop(0)
      off1 = pop.individual(2*ped)
      content[ch] += "%3d,3,%d,%d" % (ped+1, sexCode(off1), affectedCode(off1))
      content[ch] +=  genoStr(off1, ch) + '\n' 
      off2 = pop.individual(2*ped+1)
      content[ch] += "%3d,4,%d,%d" % (ped+1, sexCode(off2), affectedCode(off2))
      content[ch] +=  genoStr(off2, ch) + '\n' 
  # write to file
  for i in range(0, pop.numChrom()):
    out.write(content[i])
  out.close() 

# Load from randFam format (from many input files )
def LoadCSV(file):
  """ 
    load file from randfam CSV format
    file: input file
    For format description, please see SaveCSV
  """
  # determine files to read
  try:
    f = open(file)
    allLines = f.readlines()
  except:
    raise exceptions.ValueError("Can not open one of file " + file + ".\n" + \
      "Or file format is not correct.")
  # sex code of ranfam format
  def sexCode(code):
    if code == 1:
      return Male
    else:
      return Female
  def affectedCode(code):
    if code == 1:
      return True
    else:
      return False
  # determine loci number on each chromsome
  numLoci = []
  # lociDist[ch][ lociOrder[j] ] will be in order
  lociOrder = []
  lociDist = []
  lociNames = []
  # process the first time
  for line in allLines:
    if line[:10] == 'Chromosome':
      numLoci.append(0)
      lociOrder.append([])
      lociDist.append([])
      lociNames.append([])
      i = len(numLoci) - 1
      chInfo = line.split(',')
      numLoci[i] =  (len(chInfo)-4)/2
      names = []   # store unordered loci name
      for j in range(0, numLoci[i]):
        lociDist[i].append(float( chInfo[5+j*2]))
        lociOrder[i].append(lociDist[i][-1])
        names.append( chInfo[4+j*2].strip())
      # deal with loci order
      lociOrder[i].sort()
      for j in range(0,len(lociOrder[i])):
        lociOrder[i][j] = lociDist[i].index(lociOrder[i][j])
      # adjust loci dist
      lociDist[i].sort()
      # really add lociNames
      for j in range(0,len(lociOrder[i])):
        lociNames[i].append( names[ lociOrder[i][j] ])
  # process the second time
  # determine family structure
  i = 0
  parSizes = [0]
  offSizes = [0]
  curFam = 0
  for line in allLines:
    if line[:10] == 'Chromosome':
      if i==0:
        i = 1
        continue 
      else: # only process the first block
        break
    fam,mem = map(int,line.split(',')[0:2])
    if fam!= curFam:   # fam = 1 at first
      for j in range(curFam, fam):
        parSizes.append(0)
        offSizes.append(0)
      curFam = fam
    if mem == 1 or mem == 2:
      parSizes[fam] += 1
    else:
      offSizes[fam] += 1
  # create a population
  offPop = population( subPop=offSizes, loci = numLoci, ploidy=2,
    lociNames=lociNames, lociDist=lociDist)
  parPop = population( subPop=parSizes, loci = numLoci, ploidy=2,
    lociNames=lociNames, lociDist=lociDist)
  # process the third time 
  # fill in info
  maxAllele = 0
  curPar = 0
  curOff = 0
  curFam = 0    
  i = -1  # i is the chromosome number
  for line in allLines:
    if line[:10] == 'Chromosome':
      i += 1
      continue
    info = map(int, line.strip().split(','))
    if curFam != info[0]:
      curPar = 0
      curOff = 0
      curFam = info[0]
    # info[0] is family ID, as well as subpop id
    if info[1] == 1 or info[1] == 2: # parents
      ind = parPop.individual(curPar, info[0])
      curPar += 1
    else:
      ind = offPop.individual(curOff, info[0])
      curOff += 1        
    # get genotype of chromosome 1, ploidy 0
    geno = ind.arrAlleles(0,i)
    for loc in range(0,offPop.numLoci(i)):
      geno[loc] = info[4+2* lociOrder[i][loc] ]
    # ploidy 1
    geno = ind.arrAlleles(1,i)
    for loc in range(0,offPop.numLoci(i)):
      geno[loc] = info[5+2* lociOrder[i][loc] ]
    ind.setSex( sexCode( info[2] ))
    ind.setAffected( affectedCode( info[3]))
    if max( info[4:] ) > maxAllele:
      maxAllele = max( info[4:])
  # now we have all info, combine the pop
  pop = parPop
  pop.setAncestralDepth(1)
  pop.pushAndDiscard(offPop)
  pop.setMaxAllele(maxAllele)  
  return pop


if __name__ == "__main__":
  pass



