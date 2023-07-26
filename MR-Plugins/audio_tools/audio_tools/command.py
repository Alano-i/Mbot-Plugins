from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse,PluginMeta
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
from .audio_tools import audio_clip, move_to_dir, diy_abs, move_out,all_add_tag,add_cover
from .podcast import podcast_main,get_xml_url
import logging
import datetime
import time
import os
server = mbot_api
logger = logging.getLogger(__name__)
plugins_name = '「有声书工具箱」'
exts = ['.m4a', '.mp3', '.flac', '.wav']
move_out_config = [
    {
        "name": "🔖 DIY元数据",
        "value": 'diy'
    },
    {
        "name": "🎯 运行移出文件夹操作",
        "value": 'move'
    },
    {
        "name": "📕 整理文件夹、DIY元数据",
        "value": 'add_and_move'
    }
]
clip_config = [
    {
        "name": "📕 剪辑、整理、添加元数据",
        "value": 'clip_and_move'
    },
    {
        "name": "🎯 仅剪辑",
        "value": 'clip'
    }
]

use_filename_config_list = [
    {
        "name": "✅ 开启",
        "value": 'on'
    },
    {
        "name": "📴 关闭",
        "value": 'off'
    }
]
if server.common.get_cache('audio_clip', 'input_dirs'):
    last_time_input_dirs = uptime_input_dirs = server.common.get_cache('audio_clip', 'input_dirs')
else:
    last_time_input_dirs = '/Media/音乐/有声书/123456'

@plugin.command(name='audio_clip_m', title='音频剪辑', desc='剪辑片头片尾，修改整理元数据', icon='LibraryMusic',run_in_background=True)
def audio_clip_m_echo(ctx: PluginCommandContext,
                input_dirs: ArgSchema(ArgType.String, last_time_input_dirs, '输入路径,末尾不带/，支持多条，一行一条/Media/音乐/有声书/', default_value = last_time_input_dirs, required=False),
                output_dir: ArgSchema(ArgType.String, '输出路径', '', default_value=None, required=False),
                cliped_folder: ArgSchema(ArgType.String, '已剪辑存放路径，默认：已剪辑', '', default_value='已剪辑', required=False),
                audio_start: ArgSchema(ArgType.String, '剪辑开始时间', '默认：0，单位：秒', default_value='0', required=False),
                audio_end: ArgSchema(ArgType.String, '剪辑结束倒数秒数', '默认：0，单位：秒', default_value='0', required=False),
                clip_configs: ArgSchema(ArgType.Enum, '选择运行的操作，默认：剪辑、整理、添加元数据', '若仅剪辑，下方参数不生效。', enum_values=lambda: clip_config, default_value='clip_and_move', multi_value=False, required=False),
                use_filename_config: ArgSchema(ArgType.Enum, '文件名作为标题，默认开启', '', enum_values=lambda: use_filename_config_list, default_value='on', multi_value=False, required=False),
                authors: ArgSchema(ArgType.String, '作者：推荐填写原著作家', '', default_value=None, required=False),
                narrators: ArgSchema(ArgType.String, '演播者，多个示例：演播A,,演播B,,', '', default_value=None, required=False),
                series: ArgSchema(ArgType.String, '系列：推荐填写书名', '', default_value=None, required=False),
                year: ArgSchema(ArgType.String, '发布年份', '', default_value=None, required=False),
                albums: ArgSchema(ArgType.String, '专辑：留空则自动按每100集划分', '', default_value=None, required=False),
                art_album: ArgSchema(ArgType.String, '专辑艺术家：推荐填写书名', '', default_value=None, required=False),
                subject: ArgSchema(ArgType.String, '题材，例如：武侠，相声', '', default_value=None, required=False),
                podcast_summary: ArgSchema(ArgType.String, '简介', '用于生成播客简介', default_value='', required=False)):
    output_dir = output_dir or input_dirs
    use_filename = bool(use_filename_config and use_filename_config.lower() != 'off')
    logger.info(f"{plugins_name}任务\n开始运行音频剪辑\n输入路径：[{input_dirs}]\n输出路径：[{output_dir}/{cliped_folder}]\n开始时间：[{audio_start}]\n结束倒数秒数：[{audio_end}]\n\n整理参数如下：\n系列：['{series}']\n作者：['{authors}']\n演播者：['{narrators}']\n发布年份：['{year}']\n专辑：['{albums}']\n专辑艺术家：['{art_album}']")
    
    server.common.set_cache('audio_clip', 'input_dirs', input_dirs)
    
    
    input_dirs_s = input_dirs.split('\n')
    if albums:
        albums_s = albums.split('\n')
    album = None
    for i, input_dir in enumerate(input_dirs_s):
        if albums:
            album = albums_s[i]
        output_dir = output_dir or input_dir
        audio_clip(input_dir,output_dir,cliped_folder,audio_start,audio_end,clip_configs,authors,year,narrators,series,podcast_summary,album,art_album,use_filename,subject)
        time.sleep(5)
        try:
            audio_path = f"{output_dir}/{cliped_folder}"
            is_group = True
            podcast_main(series, audio_path, podcast_summary, subject, authors, is_group)
        except Exception as e:
            logger.error(f"「生成播客源」失败，原因：{e}")
    return PluginCommandResponse(True, f'音频剪辑任务完成')

@plugin.command(name='poscast_m', title='生成播客源', desc='生成 Apple 播客源 URL', icon='Podcasts',run_in_background=True)
def poscast_m_echo(ctx: PluginCommandContext,
                book_title: ArgSchema(ArgType.String, '书名', '', default_value = '', required=False),
                audio_paths: ArgSchema(ArgType.String, '输入路径', '支持多条，一行一条/Media/音乐/有声书/', default_value='', required=True),
                podcast_summary: ArgSchema(ArgType.String, '简介', '', default_value='', required=False),
                podcast_category: ArgSchema(ArgType.String, '分类', '', default_value='', required=False),
                podcast_author: ArgSchema(ArgType.String, '作者', '', default_value='', required=False),
                is_group_config: ArgSchema(ArgType.Enum, '第1季强制200集，默认开启', '', enum_values=lambda: use_filename_config_list, default_value='on', multi_value=False, required=False)):
    is_group = bool(is_group_config and is_group_config.lower() != 'off')
    book_title_new = book_title
    try:
        logger.info(f"{plugins_name}任务 - 生成播客源 URL\n书名：['{book_title}']\n输入路径：['{audio_paths}']\n有声书简介：['{podcast_summary}']\n有声书分类：['{podcast_category}']\n作者：['{podcast_author}']\n第1季强制200集：{is_group}")
        audio_path_list = audio_paths.split('\n')
        for i, audio_path in enumerate(audio_path_list):
            if not book_title:
                book_title_new = os.path.basename(audio_path).strip('/')
            podcast_main(book_title_new, audio_path, podcast_summary, podcast_category, podcast_author,is_group)

    except Exception as e:
        logger.error(f"「生成播客源」失败，原因：{e}")
        return PluginCommandResponse(False, f'生成博客源 RSS XML 任务失败')
    return PluginCommandResponse(True, f'生成博客源 RSS XML 任务完成')

@plugin.command(name='add_cover_m', title='修改音频封面', desc='修改音频封面', icon='Image',run_in_background=True)
def add_cover_m_echo(ctx: PluginCommandContext,
                audio_path: ArgSchema(ArgType.String, '输入路径', '/Media/音乐/有声书/', default_value='', required=True)):
    cover_art_path = os.path.join(audio_path, 'cover.jpg')
    logger.info(f"cover_art_path: {cover_art_path}")
    i=0
    try:
        for dirpath, _, filenames in os.walk(audio_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if datetime.datetime.now().second % 10 == 0 or i==0:
                    logger.info(f"{plugins_name}开始处理: {file_path}")
                add_cover(file_path,cover_art_path)
                i = i+1
        logger.info(f"{plugins_name}封面修改完成")
    except Exception as e:
        logger.error(f"「添加封面」失败，原因：{e}")
        return PluginCommandResponse(False, f'添加封面任务失败')
    return PluginCommandResponse(True, f'添加封面任务完成')

@plugin.command(name='get_xml_url', title='查看已生成播客源', desc='查看已生成 Apple 播客源 URL', icon='RssFeedSharp',run_in_background=True)
def get_xml_url_echo(ctx: PluginCommandContext,
                send_sms_config: ArgSchema(ArgType.Enum, '推送消息，默认关闭', '开启后，有多少个播客源就将收到多少条消息', enum_values=lambda: use_filename_config_list, default_value='off', multi_value=False, required=False)):
    send_sms = bool(send_sms_config and send_sms_config.lower() != 'off')
    get_xml_url(send_sms)
    return PluginCommandResponse(True, f'已生成播客源 RSS URL 获取完成')

@plugin.command(name='diy_abs', title='修改metadata.abs', desc='修改 Audiobookshelf 元数据', icon='SwitchAccessShortcutAdd',run_in_background=True)
def diy_abs_echo(ctx: PluginCommandContext,
                folder_path: ArgSchema(ArgType.String, '输入路径', '/Media/音乐/有声书/', default_value='/Media/音乐/有声书/', required=True),
                series: ArgSchema(ArgType.String, '系列：推荐填写书名', '', default_value=None, required=False),
                podcast_summary: ArgSchema(ArgType.String, '简介', '用于生成播客简介', default_value='', required=False),
                authors: ArgSchema(ArgType.String, '作者：推荐填写原著作家', '', default_value=None, required=False),
                narrators: ArgSchema(ArgType.String, '演播者，多个示例：演播A,,演播B,,', '', default_value=None, required=False),
                year: ArgSchema(ArgType.String, '发布年份', '', default_value=None, required=False)):

    logger.info(f"{plugins_name}任务\n开始运行 DIY 音频元数据\n输入路径：[{folder_path}]\n系列：['{series}']\n作者：['{authors}']\n演播者：['{narrators}']\n发布年份：['{year}']")
    diy_abs(folder_path, series, podcast_summary, authors, narrators, year)
    return PluginCommandResponse(True, f'DIY 音频元数据任务完成')

@plugin.command(name='move_to_dir', title='整理有声书', desc='分配到子文件夹 1-100 101-200 201-300, 并添加元数据', icon='RuleFolder',run_in_background=True)
def move_to_dir_echo(ctx: PluginCommandContext,
                move_out_configs: ArgSchema(ArgType.Enum, '选择运行的操作，默认：运行整理并添加元数据', '', enum_values=lambda: move_out_config, default_value='add_and_move', multi_value=False, required=False),
                output_dir: ArgSchema(ArgType.String, '输入路径', '/Media/音乐/有声书/', default_value=None, required=True),
                authors: ArgSchema(ArgType.String, '作者：推荐填写原著作家', '', default_value=None, required=False),
                use_filename_config: ArgSchema(ArgType.Enum, '文件名作为标题，默认开启', '', enum_values=lambda: use_filename_config_list, default_value='on', multi_value=False, required=False),
                narrators: ArgSchema(ArgType.String, '演播者，多个示例：演播A,,演播B,,', '', default_value=None, required=False),
                series: ArgSchema(ArgType.String, '系列：推荐填写书名', '', default_value=None, required=False),
                podcast_summary: ArgSchema(ArgType.String, '简介', '用于生成播客简介', default_value='', required=False),
                year: ArgSchema(ArgType.String, '发布年份', '', default_value=None, required=False),
                album: ArgSchema(ArgType.String, '专辑：留空则自动按每100集划分', '', default_value=None, required=False),
                art_album: ArgSchema(ArgType.String, '专辑艺术家：推荐填写书名', '', default_value=None, required=False),
                subject: ArgSchema(ArgType.String, '题材，例如：武侠，相声', '', default_value=None, required=False),
                diy_cover_config: ArgSchema(ArgType.Enum, '修改封面，默认关闭', '需要输入文件夹下有cover.jpg', enum_values=lambda: use_filename_config_list, default_value='off', multi_value=False, required=False)):
    use_filename = bool(use_filename_config and use_filename_config.lower() != 'off')
    diy_cover = bool(diy_cover_config and diy_cover_config.lower() != 'off')
    logger.info(f"{plugins_name}任务\n开始整理系列文件夹\n输入路径：[{output_dir}]\n系列：['{series}']\n作者：['{authors}']\n演播者：['{narrators}']\n发布年份：['{year}']")
    if move_out_configs == 'move':
        move_out(output_dir)
    elif move_out_configs == 'add_and_move':
        move_to_dir(output_dir,authors,year,narrators,series,podcast_summary,album,art_album,move_out_configs,use_filename,subject)
        diy_abs(output_dir, series, authors, narrators, year)
    else:
        all_add_tag(output_dir,authors,year,narrators,series, podcast_summary, album,art_album,use_filename,subject,diy_cover)
    return PluginCommandResponse(True, f'整理系列文件夹任务完成')
