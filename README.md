****
如果帮助到你，star一下，谢谢你
武汉加油，中国加油
个人时间有限，回答不过来了
目前v1出现cookie经常失效 被拒绝访问问题 正在修复
****
本代码使用方式 https://blog.csdn.net/cyz52/article/details/104177981 或者下载后阅读README.md
100M电信网络实测1-2s刷新100个商品
## 版本
- [x] python3 V1
- [x] 基于https://github.com/cycz/jdBuyMask]github V3版本制作
- [x] 已编译版本链接：链接: https://pan.baidu.com/s/1FqZP39ow_CrsAn0DfeRJ2w 提取码: 97wb

## 使用方法
- 1.修改（config.ini）：地区id、推送方式（微信、邮箱二选一）
- 2.打开exe运行

-  商品skuid修改方法（config.ini）：
1.谷歌（内核）浏览器要监控的商品url
2.按F12 ，点开Nework
3.点击需要的商品 和所在的地区
4.ctrl+f搜索 stock并点击
5.复制skuid
6.修改或者添加在config.ini内的skuids

- 地区id修改方法（config.ini）：
1.用谷歌（内核）浏览器随意打开一个京东的有货商品网页（例子：https://item.jd.com/100004770235.html）
2.右键你的收货地址并点击审查元素
3.双击并复制那串数字（xx-xx-xxxxx）
4.修改在config.ini内的area(area = xx-xx-xxxxx)

## 运行图片


## 功能
- [x] 确认是否有货
- [x] 有货自动下单
- [x] 邮件、微信（需要申请方糖api）通知
- [x] 扫码登陆
- [x] 无限个商品支持
- [x] 多线程极速刷新网页


## 更新记录
- 【2020.02.08】修复了一些bug
- 【2020.02.08】大幅优化刷新速度，增加多线程技术（可在配置调节线程数）
- 【2020.02.08】新增微信通知（http://sc.ftqq.com/3.version 查看sc_key）
- 【2020.02.08】jd-automask_V1版本上线
- 【2020.02.07】增加扫码登陆，自动保存cookie
- 【2020.02.07】V4版本，解决商品个数限制
-  Code By Rlacat

------

- 【2020.02.06】V2版本，刷新更快更频繁，通过配置文件添加商品和地区id
- 【2020.02.06】提交失败之后会继续不会暂停
- 【2020.02.06】购物车有套装商品导致解析skuid错误
- 【2020.02.05】商品有货，但是该商品已下柜，提交会报错，对部分代码进行了优化
-  Code By cycz

## 反馈问题

- 如果有红包先花掉再开脚本，不然可能需要支付密码
- 其他问题Github提issues，或者私信我！！
- 如果闪退，请打开目录jdBuyMask.txt文件查看帮助说明
- CMD界面卡住、关闭CMD的快速编辑模式就行了
