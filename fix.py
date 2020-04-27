# fd = open("commom-build.xml", "r+")
# print fd.read(4)
# fd.write(" IS")
# fd.close()

start = 0
end = 0
lines = 0
f=open("common-build.xml", "r")
contents = f.readlines()
block = False
line_offset = []
offset = 0
lines_change = []
for content in contents:
    if content.find('<path id="disallowed.ivy.jars">') > -1:
       start = lines
       # content += ''
       content = content.replace('-->','').replace('<!--','')
       content = '<!--' + content.replace('\n','') + ' -->\n'
       print(content + ' linha: '+str(start))
       
       block = True
    elif block and content.find('<antcall target="-ivy-fail-disallowed-ivy-version"/>') == -1:
        content = content.replace('-->','').replace('<!--','')
        content = '<!--' + content.replace('-->','').replace('\n','') + ' -->\n'
        # content += ''
    elif content.find('<antcall target="-ivy-fail-disallowed-ivy-version"/>') > -1:
        block = False
       
    
    lines+=1
    lines_change.append(content)
    
    
f.close()
fi=open("common-build.xml", "w")
for change in lines_change:
    fi.writelines(change)


fi.close()
# with open("common-build.xml") as f:
    # f.seek(line_offset[start])
    # if f.read().find('<path id="disallowed.ivy.jars">') > -1:
        # print(f.read())
    # print(f.readlines()[start])
 
    