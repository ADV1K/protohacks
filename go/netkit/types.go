package netkit

import (
	"context"
	"net"
	"reflect"
)

type Conn interface {
	net.Conn
}

type Server interface {
	ListenAndServe() error
	RawHandler(RawHandler)
	Handle(handler Handler)
}

type Context struct {
	context.Context
	Conn Conn
}

type ParsedMessage struct {
	Type reflect.Type
	Data []byte
}

type Parser func(conn Conn) <-chan ParsedMessage
type Encoder func(res any) ([]byte, error)
type Decoder func(req []byte, v any) error
type Handler func(ctx Context, req any) any
type RawHandler func(conn Conn)

// Wrap converts strongly typed functions into weakly typed
func Wrap[Req any, Res any](fn func(ctx Context, req Req) Res) Handler {
	return func(ctx Context, req any) any {
		return fn(ctx, req.(Req))
	}
}

func HandleKey(t reflect.Type) string {
	if t.Kind() == reflect.Ptr {
		t = t.Elem()
	}
	return t.PkgPath() + "." + t.Name()
}
