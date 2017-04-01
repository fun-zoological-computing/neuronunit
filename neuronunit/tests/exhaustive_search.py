import numpy as np
import time
import inspect
from types import MethodType
import quantities as pq
from quantities.quantity import Quantity
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import sciunit
import os, sys
thisnu = str(os.getcwd())+'/../..'
sys.path.insert(0,thisnu)
from scoop import futures
import sciunit.scores as scores
import neuronunit.capabilities as cap
import get_neab
from neuronunit.models import backends
import sciunit.scores as scores
from neuronunit.models import backends
from neuronunit.models.reduced import ReducedModel
import neuronunit.capabilities as cap
AMPL = 0.0*pq.pA
DELAY = 100.0*pq.ms
DURATION = 1000.0*pq.ms
from scipy.optimize import curve_fit
required_capabilities = (cap.ReceivesSquareCurrent,
                         cap.ProducesSpikes)
params = {'injected_square_current':
            {'amplitude':100.0*pq.pA, 'delay':DELAY, 'duration':DURATION}}
name = "Rheobase test"
description = ("A test of the rheobase, i.e. the minimum injected current "
               "needed to evoke at least one spike.")
score_type = scores.RatioScore
guess=None
lookup = {} # A lookup table global to the function below.
verbose=True
import quantities as pq
units = pq.pA


model = ReducedModel(get_neab.LEMS_MODEL_PATH,name='vanilla',backend='NEURON')
from neuronunit import tests as nutests
import copy
from itertools import repeat
import sciunit.scores as scores
import neuronunit.capabilities as cap

def model2map(iter_arg):#This method must be pickle-able for scoop to work.
    vm=VirtualModel()
    attrs={}
    attrs['//izhikevich2007Cell']={}
    param=['a','b','vr','vpeak']#,'vr','vpeak']
    i,j,k,l=iter_arg#,k,l
    model.name=str(i)+str(j)+str(k)+str(l)
    attrs['//izhikevich2007Cell']['a']=i
    attrs['//izhikevich2007Cell']['b']=j
    attrs['//izhikevich2007Cell']['vr']=k
    attrs['//izhikevich2007Cell']['vpeak']=l
    vm.attrs=attrs
    return vm


def func2map(iter_):#This method must be pickle-able for scoop to work.
    '''
    Inputs an iterable list, a neuron unit test object suite of neuron model
    tests of emperical data reproducibility.
    '''
    print(iter_)
    iter_arg,value=iter_
    assert iter_arg.attrs!=None
    model.load_model()
    import pdb
    print(iter_arg)
    print(value)
    print(value*1.01*pq.pA,model)
    model.update_run_params(iter_arg.attrs)
    #pdb.set_trace()

    import quantities as qt
    import os
    import os.path
    from scoop import utils
    score = None
    sane = False

    sane = get_neab.suite.tests[3].sanity_check(value*1.01*pq.pA,model)

    if sane == True:
        get_neab.suite.tests[0].prediction={}
        score = get_neab.suite.tests[0].prediction['value']=value*pq.pA
        score = get_neab.suite.judge(model)#passing in model, changes model

        import pickle
        pickle.dump(score, open( "save.p", "wb" ) )
        #import pdb
        #pdb.set_trace()

        model.run_number+=1
        for i in score.sort_key.values[0]:
            if type(i)==None:
                i=10.0
        error= score.sort_key.values
    elif sane == False:
        import sciunit.scores as scores
        #error = scores.InsufficientDataScore(None)
        error = [ 10.0 for i in range(0,7) ]
    return (error,iter_arg.attrs,value*pq.pA)#,score)#.related_data.to_pickle.to_python())

class VirtualModel:
    '''
    This is a pickable dummy clone
    version of the NEURON simulation model
    It does not contain an actual model, but it can be used to
    wrap the real model.
    This Object class serves as a data type for storing rheobase search
    attributes and other useful parameters,
    with the distinction that unlike the NEURON model this class
    can be transported across HOSTS/CPUs
    '''
    def __init__(self):
        self.lookup={}
        self.rheobase=None
        self.previous=0
        self.run_number=0
        self.attrs=None
        self.name=None
        self.s_html=None
        self.results=None

param=['a','b']#,'vr','vpeak']

def check_fix_range(lookup):
    '''
    Inputs: lookup, A dictionary of previous current injection values
    used to search rheobase
    Outputs: A boolean to indicate if the correct rheobase current was found
    and a dictionary containing the range of values used.
    If rheobase was actually found then rather returning a boolean and a dictionary,
    instead logical True, and the rheobase current is returned.
    given a dictionary of rheobase search values, use that
    dictionary as input for a subsequent search.
    '''
    sub=[]
    supra=[]
    for k,v in lookup.items():
        if v==1:
            #A logical flag is returned to indicate that rheobase was found.
            return (True,k)
        elif v==0:
            sub.append(k)
        elif v>0:
            supra.append(k)

    sub=np.array(sub)
    supra=np.array(supra)
                 # concatenate
    if len(sub) and len(supra):

        everything=np.concatenate((sub,supra))

        center = np.linspace(sub.max(),supra.min(),7.0)
        np.delete(center,np.array(everything))
        #make sure that element 4 in a seven element vector
        #is exactly half way between sub.max() and supra.min()
        center[int(len(center)/2)+1]=(sub.max()+supra.min())/2.0
        steps = [ i*pq.pA for i in center ]

    elif len(sub):
        steps2 = np.linspace(sub.max(),2*sub.max(),7.0)
        np.delete(steps2,np.array(sub))
        steps = [ i*pq.pA for i in steps2 ]

    elif len(supra):
        steps2 = np.linspace(-2*(supra.min()),supra.min(),7.0)
        np.delete(steps2,np.array(supra))
        steps = [ i*pq.pA for i in steps2 ]


    return (False,steps)

def check_current(ampl,vm):
    '''
    Inputs are an amplitude to test and a virtual model
    output is an virtual model with an updated dictionary.
    '''
    import copy
    if float(ampl) not in vm.lookup or len(vm.lookup)==0:
        current = params.copy()['injected_square_current']
        uc={'amplitude':ampl}
        current.update(uc)

        current={'injected_square_current':current}
        vm.run_number+=1
        model.update_run_params(vm.attrs)

        model.load_model()
        model.inject_square_current(current)
        vm.previous=ampl
        n_spikes = model.get_spike_count()
        if n_spikes==1:
            vm.rheobase=ampl
            print(vm.attrs)
            print(model.attrs)
            print('hit')
        verbose=False
        if verbose:
            print("Injected %s current and got %d spikes" % \
                    (ampl,n_spikes))
        vm.lookup[float(ampl)] = n_spikes
        return vm.lookup
        #return copy.copy(vm.lookup)
    if float(ampl) in vm.lookup:
        return vm.lookup
        #return copy.copy(vm.lookup)


def searcher(f,rh_param,vms):
    '''
    ultimately an attempt to capture the essence a lot of repeatative code below.
    This is not yet used, but it is intended for future use.
    Its intended to replace the less general searcher function
    '''
    if rh_param[0]==True:
        return rh_param[1]
    lookuplist=[]
    cnt=0
    while rh_param[0]==False and cnt<4:
        print(cnt)
        print('cnt')
        if type(rh_param[1])==float:
            d=check_current(rh_param[1],vms)
        elif len(vms.lookup)==0 and type(rh_param[1])!=float:
            returned_list=[]
            returned_list = list(futures.map(check_current,rh_param[1],repeat(vms)))
            d={}
            for r in returned_list:
                d.update(r)
        else:
            rh_param=check_fix_range(d)
            print(rh_param)
            if rh_param[0]==True:
                return rh_param[1]
                #break
            returned_list=[]
            returned_list = list(futures.map(check_current,rh_param[1],repeat(vms)))
            d={}
            for r in returned_list:
                d.update(r)
        cnt+=1
    #print(rh_param)
    return False#rh_param[1]
'''
def searcher(f,rh_param,vms):
    cnt=0
    while rh_param[0]==False and cnt<4:
        if len(vms.lookup)==0:
            d = check_current(rh_param[1],vms)
            rh_param=check_fix_range(d)
            if rh_param[0]==True:
                return rh_param[1]

        else:
            rh_param=check_fix_range(d)
            if rh_param[0]==True:
                return rh_param[1]
            returned_list2 = list(futures.map(check_current,rh_param[1],repeat(vms)))
            d={}
            for r in returned_list2:
                d.update(r)
        cnt+=1
    return False
'''

def evaluate(individual, guess_value=None):
    #This method must be pickle-able for scoop to work.
    vm=VirtualModel()
    import copy
    vm.attrs=copy.copy(individual.attrs)
    rh_param=(False,guess_value)
    print(rh_param[0])
    print(rh_param[1])

    import pdb
    pdb.set_trace()
    rheobase=searcher(check_current,rh_param,vm)#,guess_value)
    return rheobase



if __name__ == "__main__":
    #PARAMETER FILE
    '''
    vr = np.linspace(-75.0,-50.0,10)
    a = np.linspace(0.015,0.045,10)
    b = np.linspace(-3.5*10E-9,-0.5*10E-9,3)
    k = np.linspace(7.0E-4-+7.0E-5,7.0E-4+70E-5,10)
    C = np.linspace(1.00000005E-4-1.00000005E-5,1.00000005E-4+1.00000005E-5,10)
    c = np.linspace(-55,-60,10)
    d = np.linspace(0.050,0.2,10)
    v0 = np.linspace(-75.0,-45.0,10)
    vt =  np.linspace(-50.0,-30.0,10)
    vpeak =np.linspace(30.0,40.0,10)
    '''
    import model_parameters as modelp
    iter_list=[ (i,j,k,l) for i in modelp.model_params['a'] for j in modelp.model_params['b'] for k in modelp.model_params['vr'] for l in modelp.model_params['vpeak'] ]
    mean_vm=VirtualModel()
    #guess_attrs=[]
    #find the mean parameter sets, and use them to inform the rheobase search.
    guess_attrs = modelp.guess_attrs#.append(np.mean( [ i for i in modelp.a ]))
    #guess_attrs = modelp.guess_attrs#.append(np.mean( [ i for i in modelp.b ]))

    for i, p in enumerate(param):
        value=str(guess_attrs[i])
        model.name = str(model.name)+' '+str(p)+str(value)
        if i==0:
            attrs = {'//izhikevich2007Cell':{p:value }}
        else:
            attrs['//izhikevich2007Cell'][p]=value
    mean_vm.attrs=attrs


    steps = np.linspace(40,80,7.0)
    steps_current = [ i*pq.pA for i in steps ]
    model.attrs=mean_vm.attrs
    rh_param=(False,steps_current)
    rh_value=searcher(check_current,rh_param,mean_vm)
    list_of_models=list(futures.map(model2map,iter_list))

    rhstorage=list(futures.map(evaluate,list_of_models,repeat(rh_value)))
    iter_ = zip(list_of_models,rhstorage)
    score_matrixt=list(futures.map(func2map,iter_))#list_of_models,rhstorage))

    import pickle
    with open('score_matrix.pickle', 'wb') as handle:
        pickle.dump(score_matrixt, handle)

    score_matrix=[]
    attrs=[]
    score_typev=[]
    #below score is just the floats associated with RatioScore and Z-scores.
    for score,attr,_ in score_matrixt:
        for i in score:
            for j in i:
                if j==None:
                    j=10.0
        score_matrix.append(score)
        attrs.append(attr)
        print(attr,score)

    score_matrix=np.array(score_matrix)
    for i in score_matrix:
        for j in i:
            if type(j)==None:
                j=10.0
            if j==None:
                j=10.0


    with open('score_matrix.pickle', 'rb') as handle:
        matrix=pickle.load(handle)


    matrix3=[]
    for x,y in matrix:
        for i in x:
            matrix2=[]
            for j in i:
                if j==None:
                    j=10.0
                matrix2.append(j)
            matrix3.append(matrix2)
    storagei = [ np.sum(i) for i in matrix3 ]
    storagesmin=np.where(storagei==np.min(storagei))
    storagesmax=np.where(storagei==np.max(storagei))
    score0,attrs0=matrix[storagesmin[0]]
    score1,attrs1=matrix[storagesmin[1]]



    def build_single(attrs):
        #This method is only used to check singlular sets of hard coded parameters.]
        #This medthod is probably only useful for diagnostic purposes.
        import sciunit.scores as scores
        import quantities as qt
        vm = VirtuaModel()
        rh_value=searcher(check,rh_param,vms)
        get_neab.suite.tests[0].prediction={}
        get_neab.suite.tests[0].prediction['value']=rh_value*qt.pA
        score = get_neab.suite.judge(model)#passing in model, changes model

    build_single(attrs)

#    return model
    #else:
    #    return 10.0


    '''
    import pdb; pdb.set_trace()
    import matplotlib as plt
    for i,s in enumerate(score_typev[np.shape(storagesmin)[0]]):
        #.related_data['vm']
        plt.plot(plot_vm())
        plt.savefig('s'+str(i)+'.png')
    #since there are non unique maximum and minimum values, just take the first ones of each.
    tuplepickle=(score_matrix[np.shape(storagesmin)[0]],score_matrix[np.shape(storagesmax)[0]],attrs[np.shape(storagesmax)[0]])
    with open('minumum_and_maximum_values.pickle', 'wb') as handle:
        pickle.dump(tuplepickle,handle)
    with open('score_matri.pickle', 'rb') as handle:
        opt_values=pickle.load(handle)
        print('minumum value')
        print(opt_values)
    '''

                #print(j)