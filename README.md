# MCP Server 项目

## 项目概述

这是一个基于 Model Context Protocol (MCP) 的服务端实现，主要用于字符串的编码和解码操作。项目包含一个独立的编码服务模块，提供了 base64 编码/解码功能。

## 主要模块

### mcp-encoding-server

- 提供 base64 编码/解码功能
- 实现了 MCP 协议
- 支持 stdio 通信方式
- 包含完整的错误处理机制

## 快速开始

1. 克隆仓库：

```bash
git clone <repository-url>
```

2. 安装依赖：

```bash
cd mcp-encoding-server
npm install
```

3. 运行服务：

```bash
./encoding-server.js
```

## 开发指南

### 依赖要求

- Node.js (版本 16 或更高)
- npm 或 yarn

### 构建项目

```bash
npm run build
```

### 运行测试

```bash
npm test
```

## 贡献指南

欢迎提交 Pull Request。请确保：

1. 代码符合项目风格
2. 包含必要的测试用例
3. 更新相关文档

## 许可证

本项目采用 [MIT 许可证](LICENSE)

## 参考文档

- [Model Context Protocol 规范](https://github.com/modelcontextprotocol/spec)
- [MCP Filesystem Server 参考实现](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)

```

这个补充内容涵盖了项目的主要模块、快速开始指南、开发说明、贡献指南和参考文档，使 README.md 更加完整和实用。
```
