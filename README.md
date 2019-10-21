
# 打包命令
`pyinstaller -F httputils.py`


# 出现问题
* 黎明NB
RuntimeError: implement_array_function method already has a docstring   
解决：import pymysql 安装的影响
```angular2
根源：Numpy/Scipy/Pandas/Matplotlib/Scikit-learn 出现冲突

复制代码
pip uninstall scikit-learn
pip uninstall matplotlib
pip uninstall pandas
pip uninstall scipy
pip uninstall numpy

pip install numpy
pip install scipy
pip install pandas
pip install matplotlib
pip install scikit-learn

Pycharm的问题！！！
复制代码
```

* Windows server 2008 服务器上安装python 提示api-ms-win-crt-runtime-l1-1-0.dll 丢失提醒
解决方案：
https://blog.csdn.net/aitaozi11/article/details/79801980

````angular2
api-ms-win-crt-runtime就是MFC的运行时环境的库，python在windows上编译也是用微软的visual studio C++编译的，底层也会用到微软提供的C++库和runtime库，安装Visual C++ Redistributable for Visual Studio 2015 组件即可解决此问题。
安装前请删掉已有的api-ms-win-crt-runtime-l1-1-0.dll，因为VC redit.exe安装完成会重新生成。 
【C:\Windows\System32和C:\Windows\SysWOW64检查下】
是VC的一个程序：VC redit.exe 
````