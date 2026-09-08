import xml.parsers.expat as expat

with open('c:/odoo19/addons/whatsapp_web_chats/static/src/xml/chats_template.xml', 'r', encoding='utf-8') as f:
    lines = f.readlines()

stack = []

def start_element(name, attrs):
    stack.append((p.CurrentLineNumber, name))

def end_element(name):
    if stack and stack[-1][1] == name:
        stack.pop()
    else:
        top = stack[-1] if stack else ('?', 'empty')
        print('MISMATCH: closing </' + name + '> but stack top is <' + top[1] + '> opened at line ' + str(top[0]))
        print('Stack (last 5): ' + str([s[1] for s in stack[-5:]]))

p = expat.ParserCreate()
p.StartElementHandler = start_element
p.EndElementHandler = end_element

with open('c:/odoo19/addons/whatsapp_web_chats/static/src/xml/chats_template.xml', 'rb') as f:
    try:
        p.ParseFile(f)
        print('XML is valid!')
    except expat.ExpatError as e:
        print('Expat error at line ' + str(e.lineno) + ': ' + str(e))
        for i in range(max(0, e.lineno-8), min(len(lines), e.lineno+2)):
            print(str(i+1) + ': ' + lines[i].rstrip())
