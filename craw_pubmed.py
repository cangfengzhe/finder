
# coding: utf-8

# In[96]:

# 获得 id
# http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=%s' % term_name

# http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=cancer&retstart=3182080&retmax=100
# http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=212403,4584127

from common import *
from lxml.etree import *
import lxml.etree
import math
import re
import pymysql



def esearch(term, retstart, retmax, db='pubmed'):
    '''
    根据 term 查找数据库, 返回 xml
    :param term: 搜索的条目
    :param retstart: 起始位置
    :param retmax:  长度
    :param db: 数据库, 默认为pubmed
    :return: xml
    '''
    term = urllib.parse.quote(term.encode('utf-8', 'replace'))
    # urllib.parse.quote(url.encode('utf-8', 'replace'))
    str_url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=%s&term=%s&retstart=%d&retmax=%d'               % (db, term, retstart, retmax)
    request = urllib.request.Request(str_url)
    xml = urllib.request.urlopen(request).read()
    # xml = open_url(str_url, encode='utf-8')
    root = lxml.etree.XML(xml)
    return root


def get_id(term, retstart, retmax, db='pubmed'):
    '''
    返回处理后得到的id
    :param term:  搜索term
    :param retstart:
    :param retmax:
    :param db:
    :return: 返回id列表
    '''
    root = esearch(term, retstart, retmax, db)
    id_list = root.xpath('IdList/Id')
    ids = [id.text for id in id_list]
    return ids


def get_id_count(term, db='pubmed'):
    '''
    得到该 term 下的文章数目
    :param term:
    :param db:
    :return:
    '''
    root = esearch(term, 1, 1, db)
    # print(root.tostring())
    count = root.xpath('Count')[0].text
    return count


def query_id(term, retmax=100, db='pubmed'):
    '''
    核心函数
    :param term:
    :param retmax: 每页显示的id数目
    :param db:
    :return:
    '''
    count = int(get_id_count(term, db=db))
    if count > int(retmax):
        id_list = []
        for ii in range(math.ceil(count / retmax)):
            try:
                ids = get_id(term, ii * retmax, retmax, db=db)
                print('/'.join([str(ii), str(math.ceil(count / retmax))]) )
                for id in ids:
                    cu_mysql.execute('insert into pmc_id values(%s)', id)
                con_mysql.commit()
            except Exception as e:
                print(e)
                cu_mysql.execute('insert into error_pmc_id values(%s)', ii)
                con_mysql.commit()
            # id_list += ids
        # return id_list
    else:
        id_list = get_id(term, 0, count, db=db)
        for id in id_list:
            cu.execute('insert into pmc_id values(%s)', id)





    #         try:
    #             html = open_url(url, headers=headers)
    #             process_html(html)
    #             con.commit()
    #         except Exception as e:
    #             con.rollback()
    #             cu.execute('INSERT INTO error_dxy VALUES(?, ?)', (iterm, page))
    #             con.commit()


def efetch(ids, db='pubmed'):
    '''
    根据id列表获取摘要信息
    :param ids:
    :param db:
    :return:
    '''
    str_url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=%s&id=%s' % (db, ids)
    request = urllib.request.Request(str_url)
    xml = urllib.request.urlopen(request).read()
    root = lxml.etree.XML(xml)
    return root

def process_pmc(term):
    '''
    处理pmc数据库文章
    :param term:
    :return:
    '''
    root = efetch(term, db='pmc')
    articles = root.xpath('//article')
    # 对每一篇文章进行处理
    for article in articles:
        journal = article.xpath('.//journal-title')[0].text
#         journal-id journal-id-type="nlm-journal-id"
        if article.xpath('.//journal-id[@journal-id-type="nlm-journal-id"]'):
            journal_nlm_id = article.xpath('.//journal-id[@journal-id-type="nlm-journal-id"]')[0].text
        issn = article.xpath('.//issn')[0].text
        print(issn)
        title = article.xpath('.//article-title')[0].text
        subject = article.xpath('.//subject')[0].text
        pmid = article.xpath('.//article-id[@pub-id-type="pmid"]')[0].text
        pmc_id = article.xpath('.//article-id[@pub-id-type="pmc"]')[0].text
        doi = article.xpath('.//article-id[@pub-id-type="doi"]')[0].text
        authors = article.xpath('.//contrib[@contrib-type="author"]')
        year = article.xpath('.//pub-date//year')[0].text
        # 文章信息
        
     
        aff_list = article.xpath('.//aff[@id]')
        aff_dict = {}
        keywords = article.xpath('.//kwd-group//kwd')
        keyword_list = [kw.text for kw in keywords]
        keyword_join = ','.join(keyword_list)
#         ariticl_info = [pmc_id, pmid, doi, journal,journal_nlm_id, issn, title, subject, year, keyword_join]
#         print(ariticl_info)
        cu_mysql.execute('insert into pmc_ariticle(pmc_id, pmid, doi, journal,journal_nlm_id, issn, title, subject, year, keyword_join)         values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                 (pmc_id, pmid, doi, journal,journal_nlm_id, issn, title, subject, year, keyword_join))
        con_mysql.commit()
        for aff in aff_list:
            aff_str = tostring(aff)
            aff_str_tmp = re.compile(r'(?<=>)[\s\S]*(?=</aff>)').findall(aff_str.decode('utf-8'))
            if aff_str_tmp:
                aff_str = aff_str_tmp[0]
            aff_id = aff.get('id')
            aff_dict[aff_id] = aff_str
        author_index = 0
        for author in authors:
            author_index += 1
            surname = author.xpath('.//name//surname')[0].text
            given_names = author.xpath('.//name//given-names')[0].text
#             full_name = surname + given_names
            email_tmp = author.xpath('.//email')
            if email_tmp:
                email = email_tmp[0].text
            else:
                email='NA'
            # 是否通讯作者
            # <xref ref-type="corresp" rid="CR1">*</xref>
#             corres = author.xpath('.//x')
            corresp = 0
            xref_corresp = author.xpath(".//xref[@ref-type='corresp']") # [@lang='eng']
            if  xref_corresp:            
                corresp = 1
            # 通讯作者邮箱
            # 获取单位
            xref = author.xpath(".//xref[@ref-type='aff']")
            for ii in range(len(xref)):
                if(xref[ii].get('ref-type') == 'aff' ):
                    aff_name = aff_dict[xref[ii].get('rid')]
#                     print(aff_name)
                cu_mysql.execute('insert into pmc_authors(pmc_id, author_index, surname, given_names, email, corresp, aff_name)                                  values(%s, %s, %s, %s, %s, %s, %s)',
                                 (pmc_id, author_index, surname, given_names, email, corresp, aff_name))
                con_mysql.commit()
#       print(pmc_id, author_index, surname, given_names, email, corresp, aff_name)

        # 通讯作者， 邮箱， PMC有两类，一类 是
        #<contrib contrib-type="author">
#         <name>
#         <surname>Jiang</surname>
#         <given-names>Liwen</given-names>
#         </name>
#         <xref ref-type="aff" rid="A1">a</xref>
#         <xref ref-type="aff" rid="A3">c</xref>
#         <xref ref-type="corresp" rid="CR1">*</xref>
#         </contrib>
# 另一类
#     <contrib id="A3" corresp="yes" contrib-type="author">
#      以下为第二类
        corresp_authors = article.xpath('.//contrib[@corresp="yes"]')
        for corresp_author in corresp_authors:
            surname = corresp_author.xpath('.//surname')[0].text
            given_names = corresp_author.xpath('.//given-names')[0].text
#             corresp_name = surname + given_names
            email_tmp = corresp_author.xpath('.//email')
            if email_tmp:
                email = email_tmp[0].text
            else:
                email='NA'
            # pmc_id, surname, given_names, email
            cu_mysql.execute('insert into pmc_author(pmc_id, surname, given_names, email)                  values(%s, %s, %s, %s)',
                 (pmc_id, surname, given_names, email))
            con_mysql.commit()

def process_pubmed(term):
    root = efetch(term, db='pubmed')




# In[97]:

con_mysql = pymysql.connect(host='localhost', user='root', passwd='', db='xiaobaifinder', charset='utf8')
cu_mysql = con_mysql.cursor()
process_pmc('4686145')
cu_mysql.close()
con_mysql.close()


# In[95]:

cu_mysql.close()
con_mysql.close()


# In[ ]:

# pmc term
def get_pubmed_id():
    con_mysql = pymysql.connect(host='localhost', user='root', passwd='', db='xiaobaifinder', charset='utf8')
    cu_mysql = con_mysql.cursor()
    cu_mysql.execute('create table if not exists pmc_id(pmc_id varchar(12))')
    cu_mysql.execute('create table if not exists error_pmc_id(page int)')
    con_mysql.commit()
    # con = sqlite3.connect('pubmed.db')
    # cu = con.cursor()
    # # cu.execute('DROP TABLE IF EXISTS dxy')
    # cu.execute('CREATE TABLE IF NOT EXISTS pmid (pmid varchar(12))')
    # cu.execute('CREATE TABLE IF NOT EXISTS error_pmid(page int)')
    # con.commit()

    # 获取pmc id
    term = '(PRC[Affiliation] OR China[Affiliation]) AND ("2005/1/1"[PDat] : "2015/12/31"[PDat]) '
    query_id(term, db = 'pmc')

    # 获取 pmc 信息

    cu_mysql.close()
    con_mysql.close()


# In[ ]:

def get_pubmed_id():
    con_mysql = pymysql.connect(host='localhost', user='root', passwd='', db='xiaobaifinder', charset='utf8')
    cu_mysql = con_mysql.cursor()
    cu_mysql.execute('create table if not exists pubmed_id(pmc_id varchar(12))')
    cu_mysql.execute('create table if not exists error_pubmed_id(page int)')
    con_mysql.commit()
    # con = sqlite3.connect('pubmed.db')
    # cu = con.cursor()
    # # cu.execute('DROP TABLE IF EXISTS dxy')
    # cu.execute('CREATE TABLE IF NOT EXISTS pmid (pmid varchar(12))')
    # cu.execute('CREATE TABLE IF NOT EXISTS error_pmid(page int)')
    # con.commit()

    # 获取pmc id
    term = '(PRC[Affiliation] OR China[Affiliation]) AND ("2005/1/1"[PDat] : "2015/12/31"[PDat]) '
    query_id(term)
    cu_mysql.close()
    con_mysql.close()


# In[90]:




# In[ ]:



