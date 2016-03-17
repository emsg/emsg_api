#!/usr/bin/env bash
ps -ef |grep emsg_simple_api|awk '{print $2}'|xargs kill -9
rm -rf */*.pyc
rm -rf */*/*.pyc
uwsgi --http :5080 --socket :5088 --chdir `pwd` --module emsg_simple_api/wsgi &
