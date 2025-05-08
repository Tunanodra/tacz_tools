# TACZ 枪械资源包与GUI工具的映射关系

本文档详细说明了TACZ枪械资源包中各类资源如何与特定武器关联。这种关联关系对于开发能够读取枪械包并以武器为中心展示内容的GUI工具至关重要。

## 武器标识

武器的**武器ID**（如`ak47`、`m4a1`）将作为主要标识符。该ID通常是武器定义文件的文件名（不含扩展名）。

枪械包结构遵循TACZ 1.1.4标准（以`tacz_default_gun`示例为准）。文档中`[命名空间]`指枪械包特有的命名空间（如`tacz`），`[武器ID]`指武器的唯一标识符。

## 1. 武器定义

武器主要通过JSON文件定义。以下位置的文件可以标识武器：

*   **索引文件（定义）：** `data/[命名空间]/index/guns/[武器ID].json`
    *   该文件可能用于向游戏注册枪械
*   **数据文件（属性）：** `data/[命名空间]/data/guns/[武器ID].json`
    *   包含详细属性如伤害值、射速等

GUI工具应基于`data/[命名空间]/index/guns/`目录下的文件列出武器清单。

## 2. 资源分类与映射规则

对于每个已识别的`[武器ID]`，可以关联以下资源：

### 2.1. 模型（几何体）

*   **主武器模型：** `assets/[命名空间]/geo_models/gun/[武器ID].geo.json`（注：示例显示为`.json`格式，可能是基岩版几何模型格式）
*   **LOD模型（细节层级）：** `assets/[命名空间]/geo_models/gun/lod/[武器ID]_lod[N].geo.json`（如`ak47_lod1.geo.json`）

### 2.2. 纹理

*   **UV纹理（主贴图）：** `assets/[命名空间]/textures/gun/uv/[武器ID].png`
*   **HUD纹理（第一人称视角/图标）：** `assets/[命名空间]/textures/gun/hud/[武器ID]_hud.png`（命名模式可能需要确认，示例`tacz_default_gun`在`textures/gun/hud/`目录下有类似`ak47.png`的文件，可能是HUD纹理或通用纹理。`_hud`后缀是常见命名约定）
*   **物品栏图标：** `assets/[命名空间]/textures/gun/slot/[武器ID].png`（示例`tacz_default_gun`在`textures/gun/slot/`目录下有类似`ak47.png`的文件）
*   **LOD纹理：** `assets/[命名空间]/textures/gun/lod/[武器ID]_lod[N].png`

### 2.3. 显示设置（客户端）

*   **武器显示JSON：** `assets/[命名空间]/display/guns/[武器ID]_display.json`
    *   控制武器在各种UI元素、配件等中的显示方式

### 2.4. 动画

*   **基岩版动画：** `assets/[命名空间]/animations/[武器ID].animation.json`
*   **GLTF动画：** `assets/[命名空间]/animations/[武器ID].gltf`（示例显示包含GLTF文件，可能用于更复杂的动画或作为替代格式）

### 2.5. 音效

*   **音效文件目录：** `assets/[命名空间]/tacz_sounds/[武器ID]/`
    *   包含武器的各种音效文件（如`fire.ogg`、`reload.ogg`、`draw.ogg`）。GUI工具应列出该目录内容

### 2.6. 服务器端数据与逻辑

*   **数据文件（已提及）：** `data/[命名空间]/data/guns/[武器ID].json`
*   **索引文件（已提及）：** `data/[命名空间]/index/guns/[武器ID].json`
*   **合成配方：** `data/[命名空间]/recipes/gun/[武器ID].json`
*   **允许的配件标签：** `data/[命名空间]/tacz_tags/attachments/allow_attachments/[武器ID].json`
*   **自定义Lua脚本（如适用）：** 某些武器可能在`data/[命名空间]/scripts/`目录下有特定逻辑脚本。命名约定可能是`[武器ID]_gun_logic.lua`或类似（如示例中的`m870_gun_logic.lua`）

### 2.7. 玩家动画（第三人称动画）

*   与玩家模型持枪动画相关的文件：`assets/[命名空间]/player_animator/`（文件可能命名为`[武器ID]_player.animation.json`或采用其他约定。示例中包含`rifle.animation.json`、`pistol.animation.json`等文件，表明玩家动画可能基于武器类型而非特定ID进行通用映射。GUI工具开发时需谨慎考虑，可能需要关联武器数据文件中定义的通用动画类型）

## 3. 发现武器与命名空间

1.  **命名空间：** 通常可通过查看`assets/`和`data/`目录下的第一级子目录确定（如`assets/tacz/`、`data/tacz/` → 命名空间为`tacz`）。`gunpack.meta.json`文件也可能指定此信息
2.  **武器列表：** 遍历`data/[命名空间]/index/guns/`目录下的文件。该目录中每个`.json`文件（如`ak47.json`）代表一件武器，其文件名（不含扩展名）即为`[武器ID]`

## 4. GUI展示策略

GUI工具应实现以下功能：

1.  允许用户选择枪械包（文件夹或.zip文件）
2.  解析枪械包以识别命名空间和武器ID列表
3.  显示已识别的武器列表
4.  当选择某件武器时，显示其关联资源（按上述分类：模型、纹理、显示JSON、动画、音效、数据JSON、配方等）
5.  每个列出的资源应可点击，点击后尝试使用系统默认程序打开该文件

## 5. 示例：AK-47（武器ID: `ak47`）

假设命名空间为`tacz`：

*   **索引：** `data/tacz/index/guns/ak47.json`
*   **数据：** `data/tacz/data/guns/ak47.json`
*   **模型：** `assets/tacz/geo_models/gun/ak47.geo.json`
*   **UV纹理：** `assets/tacz/textures/gun/uv/ak47.png`
*   **HUD纹理：** `assets/tacz/textures/gun/hud/ak47.png`（或类似名称）
*   **物品栏图标：** `assets/tacz/textures/gun/slot/ak47.png`
*   **显示JSON：** `assets/tacz/display/guns/ak47_display.json`
*   **动画：** `assets/tacz/animations/ak47.animation.json`
*   **音效：** 目录`assets/tacz/tacz_sounds/ak47/`（包含`fire.ogg`、`reload_empty.ogg`等文件）
*   **配方：** `data/tacz/recipes/gun/ak47.json`
*   **允许的配件：** `data/tacz/tacz_tags/attachments/allow_attachments/ak47.json`

此映射关系将指导开发用于解析枪械包并向GUI提供数据的Python脚本。