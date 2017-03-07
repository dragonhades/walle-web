#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: wushuiyong
# @Created Time : 日  1/ 1 23:43:12 2017
# @Description:
import tornado.ioloop
import tornado.web
import tornado.websocket
import json
import os
from StringIO import StringIO

import cel
import os, datetime
from fabric.api import run, env, local, cd, execute, sudo
from fabric import context_managers, colors
import sql


class waller():

    '''
    序列号
    '''
    stage = ''
    sequence = 0
    stage_prev_deploy = 'prev_deploy'
    stage_post_deploy = 'post_deploy'

    stage_prev_release = 'prev_release'
    stage_post_release = 'post_release'

    version = datetime.datetime.now().strftime('%Y%m%d%H%M%s')
    project_name = ''
    dir_codebase = '/Users/wushuiyong/workspace/meolu/data/codebase'
    dir_release  = '/home/wushuiyong/walle/release'
    dir_webroot  = '/home/wushuiyong/walle/webroot'
    env.host_string = 'localhost'

    def __init__(self):
        pass

    # ===================== fabric ================
    def prev_deploy(self, SocketHandler):
        '''
        1.代码检出前要做的基础工作
        - 检查 当前用户
        - 检查 python 版本
        - 检查 git 版本
        - 检查 目录是否存在

        :return:
        '''
        self.stage = self.stage_prev_deploy
        self.sequence = 1

        command = 'whoami'
        result = run(command)

        sql.save_record(stage=self.stage, sequence=self.sequence, user_id=33,
                    task_id=32, status=1, command=command,
                    success=result.stdout, error=result.stderr)
        SocketHandler.send_to_all({
            'type': 'user',
            'id': 33,
            'command': command,
            'message': result.stdout,
        })

        command = 'python --version'
        result = run(command)

        sql.save_record(stage=self.stage, sequence=self.sequence, user_id=33,
                    task_id=32, status=1, command=command,
                    success=result.stdout, error=result.stderr)
        SocketHandler.send_to_all({
            'type': 'user',
            'id': 33,
            'command': command,
            'message': result.stdout,
        })

        command = 'git --version'
        result = run(command)

        sql.save_record(stage=self.stage, sequence=self.sequence, user_id=33,
                    task_id=32, status=1, command=command,
                    success=result.stdout, error=result.stderr)
        SocketHandler.send_to_all({
            'type': 'user',
            'id': 33,
            'command': command,
            'message': result.stdout,
        })

        command = 'mkdir -p %s' % (self.dir_codebase)
        result = run(command)

        sql.save_record(stage=self.stage, sequence=self.sequence, user_id=33,
                    task_id=32, status=1, command=command,
                    success=result.stdout, error=result.stderr)
        SocketHandler.send_to_all({
            'type': 'user',
            'id': 33,
            'command': command,
            'message': result.stdout,
        })

    def deploy(self):
        '''
        2.检出代码

        :param project_name:
        :return:
        '''

        gitUri = 'git@gitlab.renrenche.com:marketing_center/wow.git'
        # 如果项目底下有 .git 目录则认为项目完整,可以直接检出代码
        if (os.path.exists(self.dir_codebase + '/.git')):
            with cd(self.dir_codebase):
                run('pwd && git pull')
        else:
            # 否则当作新项目检出完整代码
            with cd(self.dir_codebase):
                run('pwd && git clone %s .' % (gitUri))
        pass

    def post_deploy(self):
        '''
        3.检出代码后要做的任务
        :return:
        '''
        pass

    def prev_release(self):
        '''
        4.部署代码到目标机器前做的任务
        - 检查 webroot 父目录是否存在
        :return:
        '''
        execute(self.pre_release_webroot)
        pass

    def pre_release_webroot(self):
        run('mkdir -p %s' % (self.dir_webroot))
        run('mkdir -p %s' % (self.dir_release))

    def release(self):
        '''
        5.部署代码到目标机器做的任务
        - 打包代码 local
        - scp local => remote
        - 解压 remote
        :return:
        '''
        with cd(os.path.dirname(self.dir_codebase)):
            run('tar zcvf tar.tgz %s' % (self.project_name))
            for target_server in env.hosts:
                run('scp tar.tgz %s:%s/tar.tgz' % (self.target_server, self.dir_release))

            execute(self.release_untar)
        pass

    def release_untar(self):
        '''
        解压版本包
        :return:
        '''
        with cd(self.dir_release):
            run('tar zxvf tar.tgz')

    def post_release(self):
        '''
        6.部署代码到目标机器后要做的任务
        - 切换软链
        - 重启 nginx
        :return:
        '''

        execute(self.post_release_service)

        pass

    def post_release_service(self):
        with cd(self.dir_webroot):
            run('ln -s %s %s/%s.%s.tmp' % (self.dir_release, self.dir_webroot, self.project_name, self.version))
            run('mv -fT %s.%s.tmp %s' % (self.project_name, self.version, self.project_name))
            sudo('nginx -s reload')

    def walle_deploy(self):

        # 定义项目名称
        project_name = 'wow'
        dir_codebase = '%s/%s' % (self.dir_codebase, self.project_name)
        dir_release  = '%s/%s' % (self.dir_release, self.project_name)


        # 定义远程机器
        env.hosts = ['172.16.0.231', '172.16.0.177']
        env.user  = 'wushuiyong'
        # target_server = ['127.0.0.1']

        # prev_deploy
        self.prev_deploy()

        # deploy
        self.deploy()

        # post_deploy
        self.post_deploy()

        # prev_release
        self.prev_release()

        # release
        self.release()

        # post_release
        self.post_release()

        pass
