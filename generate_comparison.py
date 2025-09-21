# -*- coding: utf-8 -*-
"""
Created on Tue Jul  1 10:38:44 2025

@author: atavo
"""

import base64,gzip,zlib,re,os,argparse
settings={}
with open('config.ini') as config:
    for line in config:
        if '=' in line:
            settings[line.split('=')[0].strip()]=line.split('=')[1].strip()
parser=argparse.ArgumentParser(description='Generates comparison between two Geometry Dash levels')
arg_group = parser.add_mutually_exclusive_group()
col_group = parser.add_mutually_exclusive_group()
parser.add_argument("input", help='space seperated list of 1,2 or 3 files;\n if only 1 file provided tries to autocomplete;\n if no extension provided presumes .gmd',nargs='+')
parser.add_argument('output',nargs='?',default=settings['default_output'],help='output')
col_group.add_argument('-d','--del_deco',help="delete all decorative objects",action="store_true")
col_group.add_argument('-v','--deco_value',help="sets the color value of decoration (0-255), defaults to 64",default=64)
arg_group.add_argument('-l','--layoutify',help="converts the level into a layout, implies -d",action="store_true")
arg_group.add_argument('-s','--strict_equivalence',help="delete all decorative objects, implies -d",action="store_true")
parser.add_argument('-b','--hitboxes',help='which levels have hitboxes, numbered 1-3, defaults to just 1',default=[1],nargs='+')
parser.add_argument('-x','--spikes',help='which levels have spike hitboxes, numbered 1-3, defaults to just 1',default=[1],nargs='+')

args=parser.parse_args()
files=args.input
deco_color=args.deco_value
del_deco=args.del_deco
has_hitboxes=args.hitboxes
has_spikes=args.spikes
#combines object with same physical properties
strict_equivalence=args.strict_equivalence
layoutify=args.layoutify
with open('replacement chart.txt') as file:
    replacements={i.split('\t')[0]:i.split('\t')[1] for i in file.read().splitlines()}
with open('object type.txt') as file:
    objtypes={i.split('\t')[0]:i.split('\t')[1][0] for i in file.read().splitlines()}
if strict_equivalence:
    del_deco=True
    with open('strict_equivalence.txt') as file:
        rel2={i.split('\t')[0]:i.split('\t')[1] for i in file.read().splitlines()}
elif layoutify:
    del_deco=True
    with open('layoutify.txt') as file:
        rel2={i.split('\t')[0]:i.split('\t')[1] for i in file.read().splitlines()}
else:
    rel2=''
assert len(files)<4, "Too many input files"
if len(files)==1:
    candidates=[]
    for path in os.listdir(settings['input_directory']):
        if files[0].lower().rsplit('.',1)[0] in path.lower().rsplit('.',1)[0]:
            candidates.append(path)
    assert len(candidates)>0, "Found nothing"
    assert len(candidates)<25, 'Search too broad'
    if len(candidates)==1:
        go=input(f"found one file: {candidates[0]}. Proceed anyway (y/n)?\n")
        if go!='y':
            raise SystemExit
    else:
        go=input('found multiple files, please select (comma sep. list of indexes):\n'+'\n'.join([f'{i[1]}: {i[0]}' for i in zip(candidates,range(len(candidates)))])+'\n')
        go=go.split(',')
        files=[]
        for index in go:
            files.append(candidates[int(index)])
        assert len(files)<4, "Too many input files"
for i in range(len(files)):
    if '.' not in files[i]:
        files[i]+='.gmd'
    if '/' not in files[i]:
        files[i]=settings['input_directory']+'/'+files[i]
color_triggers=['899','1006']
def retest(pattern,string):
    return len(re.findall(pattern, string))>0
def dec(dict_entry,dict):
    if dict_entry in dict and type(dict[dict_entry])==int:
        dict[dict_entry]-=1
    elif dict_entry in dict and type(dict[dict_entry])==str:
        dict[dict_entry]=int(dict[dict_entry])-1
    else:
        dict[dict_entry]=-1
def inc(dict_entry,dict):
    if dict_entry in dict and type(dict[dict_entry])==int:
        dict[dict_entry]+=1
    elif dict_entry in dict and type(dict[dict_entry])==str:
        dict[dict_entry]=int(dict[dict_entry])+1
    else:
        dict[dict_entry]=1
def decode_level(level_data: str, is_official_level=False) -> str:
    if level_data[:4]=='kS1,':
        return level_data
    if is_official_level:
        level_data = 'H4sIAAAAAAAAA' + level_data
    base64_decoded = base64.urlsafe_b64decode(level_data.encode())
    # window_bits = 15 | 32 will autodetect gzip or not
    decompressed = zlib.decompress(base64_decoded, 15 | 32)
    return decompressed.decode()

def encode_level(level_string: str, is_official_level=False) -> str:
    gzipped = gzip.compress(level_string.encode())
    base64_encoded = base64.urlsafe_b64encode(gzipped)
    if is_official_level:
        base64_encoded = base64_encoded[13:]
    return base64_encoded.decode()
def try_del(dict,keys):
    for key in keys:
        try:
            del dict[key]
        except:
            continue
    return dict
findex=0
def setcol(obj):
    global findex
    obj['21']=findex
    obj['22']=findex
    obj['61']=6+findex        
        
leveldata=[]
def gmd_to_list(file):
    return [i for i in re.split(r'<k>(.+?)</k>\s*(?:<[is]>(.+?)</[is]>|<t />)\s*',file.read()) if i!='']
#portals, pads and orbs
pp=[[],[],[]]
#deco
deco=[]


if del_deco:
    color_triggers.append('1007')
three=len(files)==3
used_groups=set()
def nextfree():
    i=min(set(range(1,10000))-used_groups)
    used_groups.add(i)
    return i
    raise NameError
def handle_group(group):
    group=int(group)
    if group in groupmap:
        return groupmap[group]
    elif findex>1 and group in used_groups:
        groupmap[group]=str(nextfree())
        newgroup=int(groupmap[group])
        used_groups.add(newgroup)
        return str(newgroup)
    else:
        used_groups.add(group)
        return str(group)

def handle_obj(obj):
    global replacements
    global rel2
    global objtypes
    global del_deco
    global j
    global deco
    global leveldata
    global color_triggers
    global pp
    temp={}
    for i in range(0,len(obj),2):
        if obj[i] in ['2','3','6','32']:
            temp[obj[i]]=float(obj[i+1])
        else:
            temp[obj[i]]=obj[i+1]
    obj=temp.copy()
    obj_id=obj['1']
    if '10' in obj:
        obj['10']=str(float(obj['10']))
    if obj_id=='66' and layoutify:
        if '4' in obj:
            obj['4']=1-int(obj['4'])
        else:
            obj['4']=1
        obj['1']='664'
    if obj_id in replacements:
        obj['1']=replacements[obj_id]
        if obj_id in ['29','30','105','744','900','915']:
            obj['23']={'900':'1009','105':'1004','744':'1003',
                       '915':'1002','30':'1001','29':'1000'}[obj_id]
    if obj_id in rel2:
        obj['1']=rel2[obj_id]
    obj=try_del(obj,['19'])
    obj_id=obj['1']
    #Decoration
    if obj_id not in objtypes:
        objtype='6'
        if del_deco:
            deco.append(j+len(leveldata))
        else:
            obj['21']=3+findex
            obj['22']=3+findex
            obj['61']=3+findex
            obj['24']=dec('24',obj)
    else:
        objtype=objtypes[obj_id]
        if objtype=='4':
            obj['21']=3+findex
            obj['22']=3+findex
            obj['61']=3+findex
            obj['24']=dec('24',obj)
        #Color Tiggers
        elif obj_id in color_triggers:
            if del_deco:
                deco.append(j+len(leveldata))
            else:
                temp=obj.copy()
                temp=try_del(temp,['21','22','33','35','57','36','155'])
                pp[findex-1].append((j+len(leveldata),temp.copy()))
                obj['62']=1
                obj['121']=1
                setcol(obj)
        #Remove Starting Alpha Triggers
        elif obj_id=='1007' and float(obj['2'])<30:
            if del_deco:
                deco.append(j+len(leveldata))
            else:
                temp=obj.copy()
                temp=try_del(temp,['33','57','36','155'])
                pp[findex-1].append((j+len(leveldata),temp.copy()))
                obj['62']=1
                obj['121']=1
                setcol(obj)
        #Specials
        elif objtype in 'x9':
            pp[findex-1].append((j+len(leveldata),{k:obj[k] for k in set(['1','2','3','6','32'])&set(obj.keys())}))
            obj['21']=findex
            obj['22']=findex
            obj['61']=6+findex
            obj['24']=inc('24',obj)
        #Invisible Objects
        elif obj_id in ['144','205','145','459']:
            obj['1']={'144':'216','205':'217','145':'218','459':'458'}[obj_id]
            obj['21']=findex
            obj['22']=7
            obj['61']=6+findex
        #Solid Black Center Block
        elif obj_id=='94':
            temp=obj.copy()
            obj['1']='211'
            setcol(obj)
            temp['135']='1'
            temp['20']='1'
            temp['1']='467'
            if findex not in has_hitboxes:
                temp['121']=1
            tempdata.append(temp.copy())
        elif obj_id=='1329':
            obj['1']='1614'
            if '32' in obj:
                obj['128']=1.6*float(obj['32'])
                obj['129']=2*float(obj['32'])
                del obj['32']
            elif '128' in obj:
                obj['128']=1.6*float(obj['128'])
                obj['129']=2*float(obj['129'])
            else:
                obj['128']=1.6
                obj['129']=2
            setcol(obj)
        else:
            obj['21']=findex
            obj['22']=findex
            obj['61']=6+findex
    if not del_deco or objtype!='6':
        if '33' in obj:
            obj['33']=handle_group(obj['33'])
        elif '57' in obj:
            temp=[]
            for group in obj['57'].split('.'):
                temp.append(handle_group(group))
            obj['57']='.'.join(temp)
        if '274' in obj:
            temp=[]
            for group in obj['274'].split('.'):
                temp.append(handle_group(group))
            obj['274']='.'.join(temp)
        if '51' in obj:
            obj['51']=handle_group(obj['51'])
        if '71' in obj:
            obj['71']=handle_group(obj['71'])
    obj['97']=240
    obj['96']=1
    obj['20']=findex
    if findex not in has_hitboxes and objtype not in '123':
        obj['121']=1
    if findex not in has_spikes and objtype=='2':
        obj['121']=1
    obj['64'],obj['67']=1,1
    tempdata[j]=obj
    del temp
    del obj
with open(files[0]) as file:
    groupmap={}
    findex+=1
    level=gmd_to_list(file)
    level_props={}
    for i in range(1,len(level)-1,2):
        key=level[i]
        val=level[i+1]
        try:
            level_props[key]=int(val)
        except:
            level_props[key]=val
        del key,val
    level_string=level_props['k4']
    leveldata=[]
    tempdata=decode_level(level_string)
    tempdata=tempdata.split(';')
    header,tempdata=tempdata[0],tempdata[1:-1]
    header=header.split(',')
    head_temp={}
    for j in range(0,len(header),2):
        head_temp[header[j]]=header[j+1]
        if header[j]=='kS38':
            head_temp[header[j]]=header[j+1].split('|')
    header=head_temp
    del head_temp
    if 'kS38' not in header and 'kS29' in header:
        header['kS38']=[header['kS29']+'_6_1000',header['kS30']+'_6_1001',header['kS31']+'_6_1002',header['kS32']+'_6_1004'\
                        ,header['kS33']+'_6_1',header['kS34']+'_6_2',header['kS35']+'_6_3',header['kS36']+'_6_4',header['kS37']+'_6_1003','']
        del header['kS29'],header['kS30'],header['kS31'],header['kS32'],header['kS33'],header['kS34'],header['kS35'],header['kS36'],header['kS37']
    elif 'kS38' not in header:
        to_del=[]
        for i in header:
            if 'kS' in i:
                to_del.append(i)
        for i in to_del:
            del header[i]
        header['kS38']=''
    colors=header['kS38']
    tempcolors={}
    for i in range(len(colors)-1):
        temp={}
        color=colors[i].split('_')
        for i in range(0,len(color),2):
            try:
                temp[int(color[i])]=float(color[i+1])
            except:
                temp[int(color[i])]=(float(j) for j in color[i+1].split('.'))
        tempcolors[temp[6]]=temp
        del color
    colors=tempcolors
    colors[1]={1:255,2:0,3:0,5:1,6:1,7:1,15:1,18:0,8:1}
    colors[4]={1:deco_color,2:0,3:0,5:1,6:4,7:1,15:1,18:0,8:1}
    colors[7]={1:0,2:0,3:0,5:1,6:7,7:1,15:1,18:0,8:1}
    colors[1000]={1:0,2:0,3:0,6:1000,7:1,15:1,18:0,8:1}
    colors[1001]={1:0,2:0,3:0,6:1001,7:1,15:1,18:0,8:1}
    colors[1002]={1:255,2:255,3:255,6:1002,7:1,15:1,18:0,8:1}
    colors[1009]={1:0,2:0,3:0,6:1009,7:1,15:1,18:0,8:1}
    if three:
        colors[2]={1:0,2:255,3:0,5:1,6:2,7:1,15:1,18:0,8:1}
        colors[3]={1:0,2:0,3:255,5:1,6:3,7:1,15:1,18:0,8:1}
        colors[5]={1:0,2:deco_color,3:0,5:1,11:0,12:deco_color,13:0,6:5,7:1,15:1,18:0,8:1}
        colors[6]={1:0,2:0,3:deco_color,5:1,11:0,12:0,13:deco_color,6:6,7:1,15:1,18:0,8:1}
        colors[8]={1:255,2:255,3:0,5:1,6:8,7:1,15:1,18:0,8:1}
        colors[9]={1:255,2:0,3:255,5:1,6:9,7:1,15:1,18:0,8:1}
        colors[10]={1:0,2:255,3:255,5:1,6:10,7:1,15:1,18:0,8:1}
    else:
        colors[2]={1:0,2:255,3:255,5:1,6:2,7:1,15:1,18:0,8:1}
        colors[5]={1:0,2:deco_color,3:deco_color,5:1,6:5,7:1,15:1,18:0,8:1}
    del tempcolors
    for j in range(len(tempdata)):
        obj=tempdata[j].split(',')
        handle_obj(obj)
    leveldata+=tempdata
with open(files[1]) as file:
    groupmap.clear()
    id2=len(leveldata)
    findex+=1
    temp_level=gmd_to_list(file)
    for i in range(1,len(temp_level)-1,2):
        key=temp_level[i]
        val=temp_level[i+1]
        if key=='k4':
            tempdata=decode_level(val).split(';')[1:-1]
            break
        else:
            continue
    del key,val
    for j in range(len(tempdata)):
        obj=tempdata[j].split(',')
        handle_obj(obj)
        del obj
    leveldata+=tempdata
    del tempdata,temp_level
if three:
    with open(files[2]) as file:
        groupmap.clear()
        id3=len(leveldata)
        findex+=1
        temp_level=gmd_to_list(file)
        for i in range(1,len(temp_level)-1,2):
            key=temp_level[i]
            val=temp_level[i+1]
            if key=='k4':
                tempdata=decode_level(val).split(';')[1:-1]
                break
            else:
                continue
        del key,val
        for j in range(len(tempdata)):
            obj=tempdata[j].split(',')
            handle_obj(obj)
            del obj
        leveldata+=tempdata
        del tempdata,temp_level
with open(args.output,'w') as output:
    #with open('log.txt','w') as log:
        colors='|'.join(['_'.join([f'{i}_{color[i]}' for i in color]) for color in colors.values()])+'|'
        header['kS38']=colors
        del file,colors
        ppf=[]
        ppo1=[i[1] for i in pp[0]]
        ppo2=[i[1] for i in pp[1]]
        ppo3=[i[1] for i in pp[2]]
        pp1=[]
        pp2=[]
        pp3=[]
        to_del=[]
        if three:
            for i in pp[0]:
                if i[1] in ppo2 and i[1] in ppo3:
                    to_del.append(pp[1][ppo2.index(i[1])][0])
                    to_del.append(pp[2][ppo3.index(i[1])][0])
                    ppf.append(i[0])
                elif i[1] in ppo2:
                    to_del.append(pp[1][ppo2.index(i[1])][0])
                    pp1.append(i[0])
                elif i[1] in ppo3:
                    to_del.append(pp[2][ppo3.index(i[1])][0])
                    pp2.append(i[0])
            for i in pp[1]:
                if i[1] in ppo3 and i[1] not in ppo1:
                    to_del.append(pp[2][ppo3.index(i[1])][0])
                    pp3.append(i[0])
        else:
            for i in pp[0]:
                if i[1] in ppo2:
                    to_del.append(pp[1][ppo2.index(i[1])][0])
                    ppf.append(i[0])
                else:
                    #try:
                        #log.write(f'{i[1]}\n{pp[1][pp[0].index(i)][1]}\n\n')
                    #except:
                        pass
        for i in to_del:
            leveldata[i]['135']='1'
            leveldata[i]['121']='1'
        for i in ppf:
            leveldata[i]['21'],leveldata[i]['22']='0','0'
            leveldata[i]['20'],leveldata[i]['61']='0','0'
            if 1 in has_hitboxes or 2 in has_hitboxes or 3 in has_hitboxes:
                leveldata[i]['121']=0
        for i in pp1:
            leveldata[i]['21'],leveldata[i]['22']='8','8'
            leveldata[i]['20'],leveldata[i]['61']='0','10'
            if 1 in has_hitboxes or 2 in has_hitboxes:
                leveldata[i]['121']=0
        for i in pp2:
            leveldata[i]['21'],leveldata[i]['22']='9','9'
            leveldata[i]['20'],leveldata[i]['61']='0','11'
            if 1 in has_hitboxes or 3 in has_hitboxes:
                leveldata[i]['121']=0
        for i in pp3:
            leveldata[i]['21'],leveldata[i]['22']='10','10'
            leveldata[i]['20'],leveldata[i]['61']='0','12'
            if 2 in has_hitboxes or 3 in has_hitboxes:
                leveldata[i]['121']=0
        deco+=to_del
        if del_deco:
            deco.sort(reverse=True)
            for i in deco:
                del leveldata[i]
        leveldata=','.join([ f'{i},{header[i]}' for i in header])+';'+';'.join([','.join([ f'{i},{obj[i]}' for i in obj]) for obj in leveldata])+';'
        level_string=encode_level(leveldata)
        del leveldata,header
        level_props['k4']=level_string
        del level_string
        outstring=level[0]
        for i in level_props:
            val=level_props[i]
            if val==None:
                outstring+=f'<k>{i}</k><t />'
            elif type(val)==int:
                outstring+=f'<k>{i}</k><i>{val}</i>'
            else:
                outstring+=f'<k>{i}</k><s>{val}</s>'
            del val
        outstring+=level[-1]
        del level_props,level
        output.write(outstring)
        del outstring,objtypes,pp,ppf,ppo1,ppo2,ppo3,to_del,replacements,deco,rel2,pp1,pp2,pp3,id2,findex,i,j,color_triggers
del output,three