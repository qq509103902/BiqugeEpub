#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'hipro'
__version__ = '2013.12.19'
__license__ = 'GPL'

from sys import argv, exit as esc
from urllib2 import urlopen, Request
from re import findall,sub,search, U, S
from os import chdir,walk,remove
from os.path import join,exists
from shutil import copytree, rmtree
from zipfile import ZipFile, ZIP_DEFLATED
from time import sleep


class BiqugeEpub(object):
    """docstring for BiqugeEpub"""
    def __init__(self, book_name):
        self.site = 'www.biquge.com'
        self.book_name = book_name
        self.book_id = '0'
        self.book_id_f='0'
    
    def open_url(self,url,TIMEOUT=60):
        """docstring for open_url"""
        # create request.
        req=Request(url)
        # define user-agent.
        user_agent='Chrome/32.0.1667.0 Safari/537.36'
        req.add_header('User-agent', user_agent)
        # get response
        try:
            resp=urlopen(req,None,TIMEOUT)
        except Exception as e:
            if resp:
                print resp.code, resp.msg
            else: 
                print e
        # status code 200 - 'ok'.
        if resp.code==200:
            return resp.read()
        else:
            return ""
       
    def query_book_info(self):
        """docstring for query_book_id"""
        #base_query_url="https://www.google.com.hk/search?num=1&q="
        base_query_url="http://www.baidu.com/s?rn=10&wd="
        query_operator='site:%s+intitle:"%s"' %(self.site.replace("www.", ''), self.book_name)
        url=''.join([base_query_url,query_operator])
        html=self.open_url(url)
        book_info={}
        #book_link=search('http://www\.biquge\.com/[0-9]{1,2}_([0-9]{1,9})/',html)#google
        book_link=search('www\.biquge\.com/([0-9]{1,2})_([0-9]{1,9})/',html)#baidu
        
        if book_link:
            self.book_id_f=book_link.group(1)
            self.book_id=book_link.group(2)
            book_info['bookurl']=book_link.group(0)
            print "book's url on biquge.com:",book_info['bookurl']
            if "http://" not in book_info['bookurl']: book_info['bookurl']=''.join(["http://",book_info['bookurl']])
            book_info['bookid']=book_link.group(2)
            book_info['sitename']='笔趣阁'
            #book_info['sitenameabbr']='笔趣阁'
            book_info['sitenameabbr']='本书'
            book_info['sitenamepinyin']='biquge'
            book_info['siteurl']='www.biquge.com'
            book_info['subject']='小说'
            book_info['bookname']=self.book_name
            book_info['author']=''
            book_info['authorurl']=''#'https://www.google.com.hk/search?num=1&q=%s'
            book_info['description']=''
            book_info['img_url']='http://www.biquge.com/image/%(bookidf)s/%(bookid)s/%(bookid)ss.jpg' % {'bookidf':self.book_id_f,'bookid':book_info['bookid']}
            book_info['rights']='Copyright (C) 书籍内容搜集于笔趣阁，用于轻度阅读。版权归原作者及原发布网站所有，不得用于商业复制、下载、传播'
            return book_info
        else:
            print "Could not find book information on biquge.com. Possible <biqugecom.com> has not included %s." % self.book_name
            return None        

    def generate_epub(self):
        try:
            book_info=self.query_book_info()
            
            # open book site, get book info.
            html=self.open_url(book_info['bookurl']).decode('gb18030').encode('utf-8')
            if len(html)>100:
                print "===Retrieving book information."
            subject=search('<a href="/[a-z]{4,10}xiaoshuo/">(.+?)小说</a>', html, U)
            if subject:
                book_info['subject']=subject.group(1)
            print "Subject :", book_info.get('subject')
            
            author=search('<p>作.*?者：(.+?)</p>', html, U)
            if author:
                book_info['author']=author.group(1)
                #book_info['authorurl']=book_info['authorurl'] % book_info['author']
            print "Author :", book_info['author']
            #print "Authorurl is", book_info.get('authorurl')
                  
            description=search('<div id="intro">\\s+<p>(.+?)</p>.+?</div>', html, U|S)
            if description:
                book_info['description']=description.group(1).strip().replace(' ','').replace('&nbsp;','').replace('<br>','\n')
            print "Description :", book_info.get('description')
            
            datetime=search('<p>最后更新：(.+?)</p>', html)
            if datetime:
                book_info['datetime']=datetime.group(1).strip()
            print "Last update :", book_info.get('datetime')
            
            title_all=findall('<a href="/[0-9]{1,2}_[0-9]{1,9}/([0-9]{1,9})\.html">(.+?)</a>', html, U)
            del html
            
            # Remove the cache 9 chapters.
            if len(title_all)>9: del title_all[:9]
            print 'Total Chapters:', len(title_all)
            
            # create foundation documents.
            # copy template
            if exists(self.book_id): 
                rmtree(self.book_id)
                print "===Remove old files."
                sleep(3)
            
            print "===Creating the foundation documents."                    
            copytree('epub_template',self.book_id)
            chdir(self.book_id)
            
            epub_path='../%s.epub' % self.book_name
            if exists(epub_path): remove(epub_path)
                      
            content_html=file('content.html', 'r')
            temp_con=content_html.read()
            content_html.close()            
            remove('content.html')
            
            no=3 # playOrder for ncx.
            base_url='http://www.biquge.com/%(bookidf)s_%(bookid)s/content.html' % {'bookidf':self.book_id_f,'bookid':book_info['bookid']}

            render_for={
                        'itemlist':['<item id="%(contentid)s" href="%(contentid)s.html" media-type="application/xhtml+xml" />',],
                        'itemreflist':['<itemref idref="%(contentid)s" />',],
                        'navPointlist':['<navPoint id="%(contentid)s" playOrder="%(no)s"><navLabel><text>%(title)s</text></navLabel><content src="%(contentid)s.html"/></navPoint>',],
                        'titlelist':['<li%(even_class_flag)s><a href="%(contentid)s.html">%(title)s</a></li>',],
                        }
            
            for title in title_all:
                
                html=self.open_url(base_url.replace('content',title[0])).decode('gb18030').encode('utf-8')
                content=search('<div id="content">(.+?)</div>',html,U|S)
                #content=content.decode('gb18030').encode('utf-8')
                content=content.group(1).replace('\r\n','').replace(' ','').replace('&nbsp;','').replace("<br />","<br/>").replace("<br/><br/>","</p><p>")#.replace(u'　','').replace('  ','')
                if "href=http://" in content:
                    content=sub("(href=)(http://.+?)([\\b|>])",lambda m: "".join([m.group(1),'"',m.group(2),'"',m.group(3)]),content)
                content="".join(["<p>",content,"</p>"])
                
                w_c=temp_con.replace("{{title}}",title[1]).replace("{{content}}",content)
                
                contentid="content%s_%s" % (self.book_id, title[0])
                f=file('.'.join([contentid,'html']),'w')# create content.html
                f.write(w_c)
                f.close()
                
                no+=1
                even_class_flag=('',' class="even"')[(no-3)%2] # for css
                
                render_for['itemlist'].append(render_for['itemlist'][0] % {'contentid':contentid})
                render_for['itemreflist'].append(render_for['itemreflist'][0] % {'contentid':contentid})
                render_for['navPointlist'].append(render_for['navPointlist'][0] % {'contentid':contentid, 'title':title[1], 'no':str(no)})
                render_for['titlelist'].append(render_for['titlelist'][0] % {'contentid':contentid, 'title':title[1], 'even_class_flag':even_class_flag})
                
            del title_all
            del temp_con
            
            # add page site.
            no+=1
            even_class_flag=('',' class="even"')[(no-3)%2]
            render_for['titlelist'].append(render_for['titlelist'][0].replace('html','xhtml') % {'contentid':'page', 'title':'关于%s' % book_info['sitenameabbr'], 'even_class_flag':even_class_flag})
            render_for['navPointlist'].append(render_for['navPointlist'][0].replace('html','xhtml') % {'contentid':'page', 'title':'关于%s' % book_info['sitenameabbr'], 'no':str(no)})
            
            def render(f_str):
                if '%' in f_str:
                    f_str=f_str.replace('%','%%')
                f_str=sub('(\{\{[a-z]{1,20}\}\})',lambda x:"".join(['%','(',x.group(1)[2:-2],')','s']) , f_str, U)
                f_str=f_str % book_info
                if '%%' in f_str:
                    f_str=f_str.replace('%%','%')
                return f_str
            
            # catalog.html, toc.ncx, content.opf, title.xhtml
            with file('catalog.html','r+') as cat_t, file('toc.ncx','r+') as toc_t, \
                file('content.opf','r+') as con_t, file('title.xhtml','r+') as tit_t :
                
                tit_str=tit_t.read()
                tit_str=tit_str.replace('\r',"")
                tit_t.seek(0)
                tit_t.write(render(tit_str))
                del tit_str
                
                cat_str=cat_t.read()
                cat_str=cat_str.replace('\r',"")
                cat_t.seek(0)
                
                toc_str=toc_t.read()
                toc_t.seek(0)
                
                con_str=con_t.read()
                con_t.seek(0)
                
                cat_str=cat_str.replace('{{for_titlelist}}',"\n".join(render_for['titlelist'][1:]))
                cat_t.write(render(cat_str))
                del cat_str
                toc_str=toc_str.replace('{{for_navPointlist}}',"".join(render_for['navPointlist'][1:]))
                toc_t.write(render(toc_str))
                del toc_str
                con_str=con_str.replace('{{for_itemlist}}',"".join(render_for['itemlist'][1:]))
                con_str=con_str.replace('{{for_itemreflist}}',"".join(render_for['itemreflist'][1:]))
                con_t.write(render(con_str))
                del con_str
                
            del render_for
            
            # get cover.jpg 
            jpg=file('cover.jpg','wb')
            jpg.write(self.open_url(book_info['img_url']))
            jpg.close()
            
            print '===Being generated.'
            # zip *.epub
            zip=ZipFile(epub_path,'w',ZIP_DEFLATED)
            for b,ds,fs in walk('.'):
                for ff in fs:
                    zip.write(join(b,ff))
            zip.close()
            
            print "===Cleaned temp files."
            chdir("../.") 
            rmtree(self.book_id)
            sleep(3)
            
            print '===Finish!'
            print "Epub file path is ./%s.epub." % self.book_name
            
        except Exception as e:
            #print e
            print "Fail!"
            print "Test whether you can read this novel on <biqugecom.com> with your browser. If it's okay, you can re-run program again or feedback this issue to < https://github.com/hipro/BiqugeEpub >."

def main():   
    epub=BiqugeEpub(argv[1])
    epub.generate_epub()

# def test():
#     epub=BiqugeEpub("凡人修仙传")#create a BiqugeEpub class
#     #print epub.query_book_info()
#     epub.generate_epub()
# test()

if __name__ == '__main__':
    if len(argv)<2:
        info='''Input args error, please type: "%(script)s Book_Name_You_Want".'''
        esc(info % { 'script':argv[0] })
    else:
        main()