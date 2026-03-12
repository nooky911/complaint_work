import { Form, Input, Button, Card, message } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";

import { useAuth } from "../context/AuthContext";
import api from "../api/api";
import backgroundImage from "../assets/images/background.jpg";

const LoginPage = () => {
  const { login } = useAuth();

  const onFinish = async (values) => {
    try {
      const formData = new FormData();
      formData.append("login", values.login);
      formData.append("password", values.password);

      const response = await api.post("/auth/login", formData);

      const token = response.data.access_token;
      if (token) {
        login(token);
        message.success("Успешный вход!");
      }
    } catch (error) {
      message.error(
        "Ошибка входа: " + (error.response?.data?.detail || "Ошибка"),
      );
    }
  };

  return (
    <div
      className="flex min-h-screen items-center justify-center bg-cover bg-center bg-no-repeat"
      style={{
        backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url(${backgroundImage})`,
      }}
    >
      <div className="w-full max-w-[400px] px-4">
        <Card
          title={<span className="text-lg font-bold">Вход в систему</span>}
          className="border-none bg-white/90 shadow-2xl backdrop-blur-md"
        >
          <Form name="login" onFinish={onFinish} layout="vertical" size="large">
            <Form.Item
              name="login"
              rules={[{ required: true, message: "Введите логин!" }]}
            >
              <Input prefix={<UserOutlined />} placeholder="Логин" />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: "Введите пароль!" }]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="Пароль" />
            </Form.Item>

            <Form.Item className="mb-0">
              <Button
                type="primary"
                htmlType="submit"
                block
                className="h-12 bg-blue-600 font-bold transition-colors hover:bg-blue-700"
              >
                Войти
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </div>
    </div>
  );
};

export default LoginPage;
