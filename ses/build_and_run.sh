#!/bin/bash

echo "编译Java文件..."
javac AWSSESSender.java AWSSESRequest.java

if [ $? -eq 0 ]; then
    echo "编译成功，开始运行程序..."
    java AWSSESSender
else
    echo "编译失败，请检查错误信息。"
fi