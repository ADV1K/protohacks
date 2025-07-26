package netkit

import (
	"bufio"
	"context"
	"fmt"
	"log/slog"
	"net"
	"reflect"
)

const (
	PORT       = 6969
	TCP_BUFFER = 4096 // bytes
	UDP_BUFFER = 20   // messages
)

type TCPConn struct {
	net.Conn
	buf *bufio.Reader
}

func NewTCPConn(rawConn net.Conn) *TCPConn {
	return &TCPConn{
		Conn: rawConn,
		buf:  bufio.NewReaderSize(rawConn, TCP_BUFFER),
	}
}

func (conn *TCPConn) Read(p []byte) (n int, err error) {
	return conn.buf.Read(p)
}

type TCPServer struct {
	Addr       string
	Logger     *slog.Logger
	parser     Parser
	encoder    Encoder
	decoder    Decoder
	handlers   map[string]Handler
	rawHandler RawHandler
}

func NewTCPServer(parser Parser, encoder Encoder, decoder Decoder) *TCPServer {
	return &TCPServer{parser: parser, encoder: encoder, decoder: decoder}
}

func (s *TCPServer) RawHandler(handler RawHandler) {
	s.rawHandler = handler
}

func (s *TCPServer) Handle(fn any) {
	if s.handlers == nil {
		s.handlers = make(map[string]Handler)
	}

	fnVal := reflect.ValueOf(fn)
	fnType := fnVal.Type()

	if fnType.Kind() != reflect.Func || fnType.NumIn() != 2 {
		panic("invalid handler signature")
	}

	reqType := fnType.In(1)
	resType := fnType.Out(0)

	// TODO: replace ugly reflection with sexy codegen, or try generics if they work.
	handler := func(ctx Context, req any) any {
		args := []reflect.Value{reflect.ValueOf(ctx), reflect.ValueOf(req)}
		return fnVal.Call(args)[0].Interface()
	}

	s.handlers[HandleKey(reqType)] = handler

	// Optional: you can verify return type if needed
	_ = resType
}

func (s *TCPServer) ListenAndServe() error {
	if s.Addr == "" {
		s.Addr = fmt.Sprintf(":%d", PORT)
	}

	if s.Logger == nil {
		s.Logger = slog.Default()
	}

	server, err := net.Listen("tcp", s.Addr)
	if err != nil {
		s.Logger.Error(err.Error())
		return err
	}
	s.Logger.Info(fmt.Sprintf("listening on %s", s.Addr))

	for {
		rawConn, err := server.Accept()
		if err != nil {
			s.Logger.Error(err.Error())
		}
		conn := NewTCPConn(rawConn)
		s.Logger.Info("accept connection", "addr", rawConn.RemoteAddr())

		go func(conn Conn) {
			defer conn.Close()

			if s.rawHandler != nil {
				s.rawHandler(conn)
			}

			for msg := range s.parser(conn) {
				// Decode
				req := reflect.New(msg.Type).Interface()
				err = s.decoder(msg.Data, req)
				if err != nil {
					s.Logger.Error("unable to decode request", "err", err)
					continue
				}

				// Handle
				handler, ok := s.handlers[HandleKey(msg.Type)]
				if !ok {
					s.Logger.Error("no handler for type", "type", msg.Type.String())
					continue
				}
				ctx := Context{Context: context.Background(), Conn: conn}
				res := handler(ctx, req)
				s.Logger.Info("incoming request", "type", msg.Type, "request", req, "response", res)

				// Encode
				out, err := s.encoder(res)
				if err != nil {
					s.Logger.Error("unable to encode response", "err", err)
					continue
				}

				// Send
				if _, err := conn.Write(out); err != nil {
					s.Logger.Error("write failed", "err", err)
					return
				}

			}
		}(conn)
	}
}
