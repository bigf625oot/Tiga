本项目中的Skill是基于Agno框架深度定制：
1. 没有直接使用 Agno 现成的 Skill 库，而是利用 Agno 提供的底层接口（Toolkit/Function），自己设计了一套更灵活的技能加载和管理系统。
2. 核心集成点（toolkit.py）：
   - SkillLoader：负责从不同来源加载技能（如本地文件、GitHub 仓库等）。
   - SkillValidator：负责验证技能的元数据是否符合规范。
   - SkillRegistry：负责注册和管理加载的技能，确保在运行时可以被调用。
3. 管理功能（manager.py）
   - SkillManager：负责技能的加载、验证、注册和调用。
   - SkillConfigManager：负责技能配置的加载、保存和更新。
   - Skills 类定义了如何管理技能，并设计了一套独特的 渐进式发现机制 ：
     - -  它不一次性把所有技能细节塞给 Agent。
     - -  而是先提供一个 XML 格式的技能清单（见 get_system_prompt_snippet 方法）。
     - -  Agent 需要主动调用 get_skill_instructions 等工具来按需获取详细文档或执行脚本。
4. 自定义的数据结构（skill.py& loaders/）：
   - SkillMetadata：定义了技能的元数据，包括名称、描述、兼容性等。
   - SkillConfig：定义了技能的配置，包括参数、环境变量等。
   - - Skill 类 ：定义了技能包含 instructions （说明书）、 scripts （脚本）、 references （参考资料）等属性。
   - - Loaders ：设计了可扩展的加载器（如 LocalSkills ），支持从不同来源加载技能包。

5. 总结：
   - 底层机制：Agno，利用了 agno.tools.Toolkit 和 agno.tools.function.Function 进行工具注册和调用。
   - 技能定义：自研，自己定义了“什么是技能”（包含文档、脚本、引用）
   - 交互流程：自研，设计了“浏览 -> 加载 -> 执行”的渐进式交互协议，而不是 Agno 默认的直接函数调用。
   - 加载逻辑：自研，实现了文件系统扫描和解析逻辑。
