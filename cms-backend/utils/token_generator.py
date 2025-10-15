import secrets
import string

class TokenGenerator:
    """
    用于生成指定长度的随机 token 的工具类。
    默认使用字母（大小写）和数字作为字符集，也可自定义字符集。
    """

    # 默认字符集：字母 + 数字
    DEFAULT_CHARSET = string.ascii_letters + string.digits

    @classmethod
    def generate(cls, length: int, charset: str = None) -> str:
        """
        生成指定长度的随机 token。

        :param length: token 的长度（必须为正整数）
        :param charset: 可选，自定义字符集，默认为字母+数字
        :return: 随机生成的 token 字符串
        :raises ValueError: 如果 length 不是正整数
        """
        if not isinstance(length, int) or length <= 0:
            raise ValueError("length 必须是正整数")

        if charset is None:
            charset = cls.DEFAULT_CHARSET

        if not charset:
            raise ValueError("字符集不能为空")

        return ''.join(secrets.choice(charset) for _ in range(length))

    @classmethod
    def generate_alphanumeric(cls, length: int) -> str:
        """生成仅包含字母和数字的 token"""
        return cls.generate(length, cls.DEFAULT_CHARSET)

    @classmethod
    def generate_hex(cls, length: int) -> str:
        """生成十六进制格式的 token（0-9, a-f）"""
        return cls.generate(length, string.hexdigits.lower())

    @classmethod
    def generate_numeric(cls, length: int) -> str:
        """生成纯数字的 token"""
        return cls.generate(length, string.digits)

    @classmethod
    def generate_complex(cls, length: int) -> str:
        """生成包含大小写字母、数字和特殊字符的强 token"""
        complex_charset = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
        return cls.generate(length, complex_charset)


# 使用示例
if __name__ == "__main__":
    print("默认（字母+数字）:", TokenGenerator.generate(16))
    print("十六进制:", TokenGenerator.generate_hex(16))
    print("纯数字:", TokenGenerator.generate_numeric(10))
    print("复杂字符:", TokenGenerator.generate_complex(12))